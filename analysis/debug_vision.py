"""
debug_vision.py
Usage: python analysis/debug_vision.py <POST_ID>
Purpose: Force analyze a single post to debug why it is remaining null.
"""
import sys
import os
import time
import json
import traceback
import requests
import tempfile
import google.generativeai as genai
from supabase import create_client
from dotenv import load_dotenv

# 1. Setup Environment
load_dotenv()
supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Use the correct model
MODEL_NAME = "gemini-2.5-flash"  # 或 gemini-2.0-flash-exp (如果你的 Key 支援)

def download_image_stealth(url):
    print(f"   ⬇️ Downloading: {url[:50]}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://www.threads.net/"
    }
    try:
        resp = requests.get(url, headers=headers, stream=True, timeout=15)
        if resp.status_code != 200:
            print(f"   ❌ HTTP Error: {resp.status_code}")
            return None
        
        fd, path = tempfile.mkstemp(suffix=".jpg")
        with os.fdopen(fd, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return path
    except Exception as e:
        print(f"   ❌ Download Exception: {e}")
        return None

def analyze_single_post(post_id):
    print(f"🔍 Fetching Post ID: {post_id}")
    
    # 1. Fetch from DB
    resp = supabase.table("threads_posts").select("*").eq("id", post_id).execute()
    if not resp.data:
        print("❌ Post not found in Supabase!")
        return

    post = resp.data[0]
    images = post.get("images") or []
    
    if not images:
        print("⚠️ No images found in this post.")
        return

    print(f"📸 Found {len(images)} images. Starting analysis...")
    
    updated_images = []
    any_change = False
    
    for i, img in enumerate(images):
        print(f"\n--- Processing Image {i+1}/{len(images)} ---")
        
        # Determine URL
        src = img.get("cdn_url") or img.get("original_src") or img.get("src")
        if not src:
            print("   ⚠️ No valid URL found.")
            updated_images.append(img)
            continue
            
        if img.get("scene_label"):
             print(f"   ℹ️ Already analyzed: {img.get('scene_label')}")
             # Uncomment next line if you want to FORCE re-analyze even if it exists
             # pass 
             updated_images.append(img)
             continue

        # Download
        local_path = download_image_stealth(src)
        if not local_path:
            print("   ❌ Skip: Download failed.")
            img["scene_label"] = "download_failed"
            updated_images.append(img)
            any_change = True
            continue

        # Analyze
        try:
            print("   🧠 Sending to Gemini...")
            myfile = genai.upload_file(local_path)
            
            prompt = """
            Return JSON ONLY. Keys: scene_label, full_text, context_desc.
            scene_label options: food, meme, selfie, scenery, screenshot, other.
            """
            
            model = genai.GenerativeModel(MODEL_NAME)
            result = model.generate_content(
                [myfile, prompt], 
                generation_config={"response_mime_type": "application/json"}
            )
            
            parsed = json.loads(result.text)
            print(f"   ✅ Gemini Result: {parsed}")
            
            img.update(parsed)
            updated_images.append(img)
            any_change = True
            
            # Cleanup
            myfile.delete()
            
        except Exception as e:
            print(f"   🔥 Gemini Error: {e}")
            traceback.print_exc()
            img["scene_label"] = "analysis_failed"
            updated_images.append(img)
            any_change = True
        finally:
            if os.path.exists(local_path):
                os.remove(local_path)
                
    # 3. Update DB
    if any_change:
        print(f"\n💾 Updating Supabase for Post {post_id}...")
        try:
            res = supabase.table("threads_posts").update({"images": updated_images}).eq("id", post_id).execute()
            print("✅ DB Update Successful!")
            print(f"   Updated Data: {res.data}")
        except Exception as e:
            print(f"❌ DB Update FAILED: {e}")
            traceback.print_exc()
    else:
        print("\n💤 No changes needed.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analysis/debug_vision.py <POST_ID>")
    else:
        analyze_single_post(sys.argv[1])