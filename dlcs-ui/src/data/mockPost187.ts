import { PostAnalysis } from "../types/analysis";

export const mockPost187: PostAnalysis = {
  meta: {
    Post_ID: "187",
    Timestamp: "2025-12-08T21:52:19.462118",
    High_Impact: false,
  },
  quant: {
    Sector_ID: "Sector_A",
    Primary_Emotion: "Cynicism",
    Strategy_Code: "MORAL_FRAMING",
    Civil_Score: 4,
    Homogeneity_Score: 0.87,
    Author_Influence: "Medium",
  },
  stats: {
    Likes: 0,
    Replies: 0,
    Views: 81000,
  },
  insights: {
    "0": {
      name: "務實憂慮者",
      summary: "表達對當選人僅為薪酬而任職、未必履行職責的直接擔憂。",
      pct: 0.107,
    },
    "1": {
      name: "犬儒批評者",
      summary: "透過辛辣嘲諷與戲謔，質疑整個選舉制度的認受性及當選人的能力。",
      pct: 0.714,
    },
  },
  discovery: {
    Sub_Variant_Name: "Transactional_Devaluation",
    Is_New_Phenomenon: false,
    Phenomenon_Description:
      "The act of reframing a political achievement as purely transactional, eroding its legitimacy and symbolic power.",
  },
  section1: {
    executiveSummary:
      "貼文在表面祝賀中隱藏反諷，留言區迅速轉為犬儒嘲諷，主要關切選舉的工具性與制度可信度。",
    phenomenonSpotlight:
      "從『被選上就領薪水』的戲謔出發，快速引發對整個制度的認受性質疑。",
    l1DeepDive:
      "語氣帶有戲謔式斷言，表面提問實則貶抑，常用反問與冷笑詞彙。",
    l2Strategy:
      "主策略為 Moral Framing + Cynical Detachment，透過道德對比顯得當選人不配。",
    l3Battlefield:
      "兩大派系：犬儒批評者佔多數且高互動；務實憂慮者聲量小但想提醒實務責任。",
    factionAnalysis:
      "犬儒派掌握頭部讚數，將話題導向制度荒謬；務實派則在尾段補充，未能帶動共鳴。",
    strategicImplication:
      "此場域呈現低風險的日常化抵抗，對制度信任度與官方敘事造成慢性侵蝕。",
    academicReferences: [
      { author: "Searle", year: "1969", note: "Illocutionary acts framing the mock praise." },
      { author: "Fairclough", year: "1995", note: "Discourse practice revealing institutional legitimacy struggles." },
      { author: "Scott", year: "1985", note: "Weapons of the Weak: quotidian resistance via sarcasm." },
    ],
  },
  strategies: [
    {
      name: "Moral Framing",
      intensity: 0.8,
      description: "對比『領薪水』與『應有責任』以凸顯道德落差。",
      example: "冇心做嘢都可以攞人工？",
      citation: "Fairclough 1995",
    },
    {
      name: "Cynical Detachment",
      intensity: 0.9,
      description: "以玩笑形式切斷對政治承諾的信任。",
      example: "領完薪水走人啦，做咩仲裝認真？",
      citation: "Scott 1985",
    },
    {
      name: "Playful Irony",
      intensity: 0.6,
      description: "用輕快口吻包裝嘲諷以降低風險。",
      example: "咁都得？真係天下武功唯快不破。",
      citation: "Martin & White 2005",
    },
  ],
  tone: {
    assertiveness: 0.72,
    cynicism: 0.88,
    playfulness: 0.64,
    contempt: 0.55,
    description: "戲謔式斷言，表面提問、實為貶抑，帶有冷感旁觀。",
    example: "選到就有人工，做唔做到唔緊要啦。",
  },
  factions: [
    {
      label: "犬儒批評者",
      dominant: true,
      summary: "以辛辣嘲諷質疑制度及當選人。",
      bullets: ["高互動量、掌握頭部按讚", "擅用戲謔與貶抑", "將焦點轉向制度荒謬"],
    },
    {
      label: "務實憂慮者",
      dominant: false,
      summary: "強調履職與公共責任，聲量偏小。",
      bullets: ["關注實際執行", "用平實語氣提醒責任", "互動量較低"],
    },
  ],
  commentSamples: [
    {
      author: "@hau__cho",
      text: "咁都叫成功？領薪水先係重點啦。",
      likes: 1200,
      faction: "犬儒批評者",
      tags: ["Cynicism", "Irony"],
    },
    {
      author: "@pragmatichk",
      text: "希望唔好淨係簽到，真係要做嘢。",
      likes: 320,
      faction: "務實憂慮者",
      tags: ["Concern", "Duty"],
    },
    {
      author: "@lol_but_true",
      text: "咁既制度仲講專業？笑死。",
      likes: 850,
      faction: "犬儒批評者",
      tags: ["Sarcasm"],
    },
  ],
  narrativeShift: [
    { stage: "Post", label: "Public service / 政治理想" },
    { stage: "Head", label: "功能性嘲諷" },
    { stage: "Mid", label: "犬儒批評擴散" },
    { stage: "Tail", label: "制度失望 / 無力感" },
  ],
};
