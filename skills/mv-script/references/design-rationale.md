# 設計理由

每條規則一列：規則｜來源｜理由。來源分五類：

| 標記 | 意思 |
| --- | --- |
| AutoMV | 論文與 repo（音樂驅動 MV，多 agent） |
| ViMax | repo 的分鏡與機位提示（點子或劇本到影片） |
| OpenDirector | repo 的 10 行模板與 `@Name` 引用（一句話到分鏡圖影片） |
| LUNA 實戰 | 作者自己做的一支 MV 在 P1／P2 製作過程中決定的做法（該專案的劇本不隨本外掛公開） |
| P3–P4 教訓 | 參考圖、關鍵幀、試作階段發現劇本寫法做不到 |

「三家都沒有、自己補」的規則標「自補」，來源欄寫三家都沒有的證據。研究依據是三個開源專案的程式碼與 prompt（AutoMV 另依論文 arXiv 2512.12196）。

## 一、結構與分層

| 規則 | 來源 | 理由 |
| --- | --- | --- |
| 名詞表加 `@id` 引用：story 與 shots 只准用 `@id`，不得用別名 | AutoMV、ViMax、OpenDirector | 三家都有角色版。AutoMV 的消融實驗：拿掉角色庫，角色一致性分數從 3.07 掉到 1.22（整體專家分數 2.42 降到 1.84）。OpenDirector 規定名稱「必須完全一致」並用 `@Name` 引用。我們擴大到道具、場景、特效、狀態 |
| 名詞表要涵蓋非角色實體（object、place、vfx、state） | LUNA 實戰、自補 | AutoMV 的角色庫「只管人，不管道具、物件、場景或特效」；ViMax 沒有物件／特效 glossary，靠每鏡重複描述；OpenDirector 的道具只存文字。實戰中的歧義多半出在非角色名詞（光、框、白） |
| 先定義再引用，不是事後從劇本推導 | AutoMV | AutoMV 的角色庫是「事後」從 `story.json` 推導，不是先定義後引用，名稱靠對應，實際輸出是 "The Woman" |
| 每個實體寫 `not_this`（容易誤會成什麼） | LUNA 實戰、自補 | 研究建議的 `not_to_be_confused_with`；實戰中 critic 最常抓到的是「同色或相近的東西靠什麼分辨」 |
| `aliases_forbidden`：禁用別名，出現就 FAIL | ViMax、OpenDirector | ViMax 的 `character_extractor` 規定「同一實體的多種稱呼要歸到同一個角色，選一個識別名」；OpenDirector 只掃 `@Name` 不驗證存在，我們補上「找不到就報錯」 |
| 敘事層與鏡頭層分開：story 只寫劇情，不寫畫面細節 | OpenDirector | 劇本層提示：「focus on high-level plot actions only. Keep it abstract」，不寫背景、鏡頭、舞台指示；具體畫面全部放鏡頭層 |
| 敘事混入鏡頭用語給 WARN（N3） | OpenDirector、LUNA 實戰 | 同上；程式可檢查，不必靠人 |
| 首幀與運動分開 | ViMax、OpenDirector | ViMax：首尾幀描述是「純快照，不含進行中動作」；OpenDirector：`STATIC_ACTION` 禁止動作、轉場、前後時序，運動只寫在影片 prompt。對應我們「關鍵幀到 I2V」的流程 |
| 運動分 `camera` 與 `subject` | ViMax、OpenDirector | ViMax：「必須清楚區分鏡頭運動和畫面內運動」；OpenDirector：影片 prompt 只寫鏡頭運動與主體動作 |
| `last_frame` 必須等於首幀加上運動的結果 | ViMax | 「末幀描述必須與首幀、運動描述邏輯一致；運動裡的每個動作都要反映在末幀」 |
| `variation`（small／medium／large）決定要不要寫末幀 | ViMax | ViMax 的 `variation_type` 決定要不要生末幀：small 只用首幀，medium／large 才生末幀並兩張一起餵影片模型。可直接決定用一般 I2V 還是首尾幀模式 |
| 每鏡必填 `transition_in`，限定 vocab 值與參數 | 自補 | 三家都沒有轉場欄位：AutoMV 直接 concat；ViMax 只有硬切，提示固定寫 "The transition between the shots is a cut to."；OpenDirector Creative 模式沒有。實戰的 v1 劇本反覆出現「漏了轉場」 |
| `match_cut` 必須寫 `note`（對齊什麼） | LUNA 實戰 | 審稿時發現：兩鏡裡同一個形狀大小差了好幾倍，只寫「位置對齊」，讓人不知道對齊什麼 |
| `beat_events` 一拍一筆，不寫「閃三次」 | 自補 | AutoMV 與研究建議把「3、2、1」寫成逐拍陣列（`beats: [{t, show}]`）；三家都沒有這種欄位。W3 檢查序列詞 |
| 時間位置用 `[小節, 拍]`，`span.to` 不含在鏡內，首尾相接 | 自補、LUNA 實戰 | OpenDirector 把場景時長平均分給各鏡，無時間軸概念，不可借；ViMax 無音樂。音樂驅動的來源是 timeline，所以位置必須落在拍點（T1），鏡頭首尾相接（T3） |
| 切點最終用絕對幀號，不用時長累加 | LUNA 實戰 | 累加會有誤差；`frame = round(t × fps)` 由下游讀 timeline |
| 鏡頭長度上限 `max_shot_bars` | AutoMV、LUNA 實戰 | AutoMV 的 hard rule：每段 3–8 秒、最長不超過 15 秒；實戰中上限定為 2 小節，避免後半段角色漂移 |
| route C（視差）不超過 1 小節、不用於特寫、主體動作只能後製（S6） | LUNA 實戰 | 視差是靜態圖加小位移；特寫走視差會暴露假；主體要動就必須有影片模型或後製 |
| 畫面內不得有文字（`brand_text: post_only`） | AutoMV、LUNA 實戰 | AutoMV 論文自列的問題之一是「畫面文字亂碼」；OpenDirector 的 `PROPS` 規定「Avoid readable text, subtitles, UI, logos, and watermarks」。字標與字卡只在後製疊 |
| `status`（proposed／confirmed）與 `questions` 的生命週期 | LUNA 實戰 | 使用者不必翻整份檔案找「哪些還沒確認」；lint 把它們全部列為 OPEN |

## 二、ViMax 寫法規則

| 規則 | 來源 | 理由 |
| --- | --- | --- |
| 每個元素寫位置、大小、面向（`subjects[].placement`、`size`、`facing`） | ViMax、OpenDirector | ViMax：「描述畫面元素時必須標明在畫面中的位置」「描述人物時一定要寫面向哪個方向」；OpenDirector `SUBJECTS`：placement、relative size、facing/gaze、visibility/occlusion |
| 特寫要寫聚焦部位（lint V1） | ViMax | 「特寫時要說明聚焦在哪個身體部位」 |
| 不准比喻（lint V2） | ViMax | 「No metaphors allowed!!!」「避免比喻與情緒修辭，只寫可視覺化的資訊」；比喻讓執行者不知道要畫什麼 |
| 不寫看不見的東西 | ViMax | 「Ensure that invisible elements are not included」 |
| 用具體動作，不用抽象情緒 | ViMax | 「Use concrete actions instead of abstract emotions」 |
| 不發明新角色、物件、地點、事件 | OpenDirector | 「Do not invent new characters, objects, locations, plot beats, or outcomes」；對應我們的 R1（`@id` 必須存在） |
| 左右一律是觀眾視角，角色自己的左右寫 `char_left`／`char_right` | LUNA 實戰 | 角色的左右和畫面的左右在背面與側面會相反；實戰中有數十張訓練資料因為配件畫在錯的一側而被淘汰 |

## 三、審稿與流程

| 規則 | 來源 | 理由 |
| --- | --- | --- |
| lint 加 critic 兩層：程式查結構，LLM 查語意 | 自補 | AutoMV 的 critic 只審「生成後的單張圖」，影片審查甚至被寫死成永遠通過（`judge_result = "yes"`、`current_score = 5`）；ViMax 的 ScriptEnhancer 沒接進主流程；OpenDirector 沒有審查。三家都沒有「審劇本文字」 |
| critic 只找歧義、不評美感 | LUNA 實戰 | 評美感會讓題目爆量、淹掉真正會做錯的題；邊界是「讀錯或要人猜的地方」 |
| critic 用乾淨脈絡、只看檔案 | LUNA 實戰 | 讀者必須是「只拿到檔案、要親手畫出關鍵幀的人」，才抓得到作者自己看不出的省略 |
| critic 範圍排除 lint 已做的項目 | LUNA 實戰 | 避免重複，並讓 critic 專注語意 |
| critic 不重複已解決與已列在 `questions` 的題 | LUNA 實戰 | 否則每一輪都要重處理舊題 |
| 精度題 Claude 代決並記錄理由；劇情與設定題問使用者 | LUNA 實戰 | 使用者曾對一整段的 31 題審稿授權「全部由你來決定」；但劇情、設定仍「越多越好，不要猜」。給決策表，不給問題清單 |
| 兩種授權模式，代決標「Claude 代決」並延後重審 | LUNA 實戰 | 使用者曾授權「自行完成所有任務直到 P3 結束」；為避免代決的劇情被當成已確認，鏡頭維持 `proposed`，延後到下一關卡集中審 |
| 多鏡重複的特效先做示意，使用者確認才寫進 shots | P3–P4 教訓 | 見第四節第 8 條 |
| 逐段寫，每段 lint 加 critic 加使用者確認後 commit | LUNA 實戰 | 一次寫完整片，錯誤會跟著後面所有鏡頭走 |
| 全片寫完後才重寫 style bible | LUNA 實戰 | 風格規範要涵蓋所有場景與色票；先寫會跟後面的鏡頭矛盾 |
| 線上文件是產物，只替換變動的區塊 | LUNA 實戰 | 線上文件的版面是手動排版的，整份重貼會洗掉 |
| 文件 id 與 body node id 記在 `project.yaml` | LUNA 實戰 | 換工作階段後靠它找到文件 |
| 概念階段先提 3 個方向 | LUNA 實戰 | 使用者挑選或混合，比一開始寫完整劇本便宜 |
| 參數逐項問使用者，不替使用者選 | LUNA 實戰 | 「v1 mv_plan 填補空白靠猜，造成使用者要自己找的矛盾」 |
| 拍點用 stem 做客觀驗證，不靠使用者聽 | LUNA 實戰（P1） | 聽感會被人聲與延遲誤導 |
| 英文 hook 的人聲時間用 onset 偵測，不用 whisper | LUNA 實戰（P1） | 在「3、2、1、GO」這類短 hook 上，onset 比 whisper 字詞時間穩 |
| JSON Schema（結構）與 lint（語意）分兩層 | 自補 | 結構可以替換，語意跟著流程走；OpenDirector 用 zod 強制結構輸出、AutoMV 只有淺層 JSON |

## 四、P3–P4 教訓與對應規則

| 規則 | 來源 | 理由 |
| --- | --- | --- |
| 每個非角色實體都要有 `refs:` | P3–P4 教訓 | 少見的載具與艙體只靠文字畫不出來；P3 先出固定參考圖，寫回 `refs` |
| 凍結、定格要寫 `read_as` | P3–P4 教訓 | 定格在半空看起來像飄浮，要說明觀眾應看成什麼並補線索 |
| 物件比例與仰角要寫（`size`、`angle`、機位） | P3–P4 教訓 | 物件比例與仰角在生成時會跑掉；沒有錨就沒有東西能校正 |
| P4-1：移動或轉向的主體，`facing` 依階段寫（lint F2） | P3–P4 教訓 | 一個從畫面側邊滑入的飛行夥伴，滑行時朝行進方向，停下才轉正；單一值無法表達 |
| P4-2：兩個 beat_event 之間的動作量要和時長相符，位移或轉身至少約 1 拍（lint F4） | P3–P4 教訓 | 13 幀要滑入、減速再轉身，模型實際需要約 2.8 s，後製只好加速 4–6 倍，動作很急 |
| P4-3：不動的角色要寫表情、嘴、眼（lint F3） | P3–P4 教訓 | 模型讓角色嘴巴微張 |
| P4-4：外觀在一鏡內會變，不論 variation 都要有 `last_frame`（lint F1） | P3–P4 教訓 | 沒有尾幀時，瞳孔顏色漂掉 |
| P4-5：同一主體的位置、大小數字要自洽（critic 12.5） | P3–P4 教訓 | 「高為畫面 1/4、頂端在 70%」又要「底座在地面圓心」，三者互相矛盾 |
| P4-6：位置優先錨定場景元素，百分比當輔助（critic 12.6） | P3–P4 教訓 | 寫「畫面水平置中」，結果偏了 26 px |
| P4-7：精確數量標明近似或改後製（critic 12.7） | P3–P4 教訓 | 「剛好 12 扇窗」「7 欄 × 3 層」，生成模型做不到精確 |
| P4-8：多鏡重複的特效先做示意 | P3–P4 教訓 | 「特效先閃 3 幀彩色再變單色」，看到示意後改成「直接以單色出現」 |
| P4-9：選填 `model_hint` 依鏡頭內容分流（critic 12.9） | P3–P4 教訓 | 首尾幀模型對眼瞼等細部動作很弱，會變成溶接，特寫的細部動作不要派給它 |
| 「畫面高 N%」從上緣量起 | LUNA 實戰 | 同一段內兩種量法混用，造成位置互相矛盾；寫進格式說明統一 |
| 首幀不含轉場效果，轉場疊在它上面 | LUNA 實戰 | 審稿時發現：first_frame 是淡入前還是淡入後無法判斷 |

## 五、lint 代碼

| 代碼 | 規則 | 來源 | 理由 |
| --- | --- | --- | --- |
| G1 | 實體必填 kind、name、status、definition | OpenDirector、ViMax | 集中定義才有東西可引用 |
| G2 | 非角色缺 `look` 給 WARN | AutoMV、LUNA 實戰 | 沒有外觀就無法畫出來 |
| R1 | `@id` 必須在名詞表 | OpenDirector | OpenDirector 只掃不驗，我們補上報錯 |
| R2 | 禁用別名與禁用母題 FAIL | ViMax、LUNA 實戰 | 同一東西只能一個名字；禁用母題（例如曾被使用者否決的設定）全文掃描 |
| R3 | 寫了實體名稱沒寫 `@id` 給 WARN | LUNA 實戰 | 名稱容易漂成別名 |
| T1 | `span` 必須落在拍點、to 晚於 from | 自補 | 音樂驅動的時間來源是 timeline |
| T2 | 鏡頭長度上限 | AutoMV、LUNA 實戰 | 見第一節 |
| T3 | 鏡頭首尾相接、第一鏡從 `[0,0]` | 自補 | 避免黑洞與重疊 |
| T4 | 鏡頭起點在所屬段落內 | LUNA 實戰 | 段落與鏡頭對不上會讓 story 與 shots 脫節 |
| T5 | `beat_events` 在鏡頭時間內且有 `event` | 自補 | 事件落在鏡外等於沒寫 |
| T6 | 回報鏡頭覆蓋到幾秒 | LUNA 實戰 | 看出尚未寫完的段落 |
| S1 | 必填欄位 | OpenDirector | 固定欄位模板加必填規則 |
| S2 | `shot_size`、`angle`、`route`、`variation`、`story_beat`、歌詞 id 的值 | ViMax、OpenDirector | 詞彙是封閉集合，才能被下游展開 |
| S3 | 主體有位置、大小；角色有 `facing`、`state` | ViMax | 見第二節 |
| S4 | 運動詞彙與 `realize`；medium、large 必須有末幀 | ViMax | variation 規則 |
| S5 | 轉場類型與參數 | 自補 | 三家都沒有轉場 |
| S6 | route C 的限制 | LUNA 實戰 | 見第一節 |
| S7 | 畫面裡寫到的實體要列在 subjects | ViMax | 「所有可見角色都要描述」；沒列就沒有位置與大小 |
| W1 | 首幀不寫動作詞 | ViMax、OpenDirector | 首幀是快照 |
| W2 | 模糊詞 | LUNA 實戰 | 「一些、某種、大概」等無法執行 |
| W3 | 序列要拆成 `beat_events` | 自補 | 見第一節 |
| N1、N2 | 每個段落有敘事、bars 與 timeline 一致 | LUNA 實戰 | 敘事層對得上時間軸 |
| N3 | 敘事混入鏡頭用語 | OpenDirector | 見第一節 |
| Y1 | 值裡的「 #」被 YAML 當成註解 | LUNA 實戰 | 色碼 `#29d3f5` 曾被吃掉，只剩前半段 |
| X1 | 結構不符 schema | OpenDirector | zod 強制結構輸出；我們以 JSON Schema 做可替換的結構層 |
| V1 | 特寫要寫聚焦部位 | ViMax | 見第二節 |
| V2 | 不准比喻 | ViMax | 見第二節 |
| F1 | 外觀會變要有 `last_frame` | P3–P4 教訓 | P4-4 |
| F2 | 位移或轉向的主體 `facing` 依階段 | P3–P4 教訓 | P4-1 |
| F3 | 靜止角色的首幀寫表情、嘴、眼 | P3–P4 教訓 | P4-3 |
| F4 | 相鄰拍點不到 1 拍卻含位移 | P3–P4 教訓 | P4-2 |

## 六、P5 以後

| 規則 | 來源 | 理由 |
| --- | --- | --- |
| 圖像 prompt 用 10 行固定標籤模板，由程式從欄位組出 | OpenDirector | 「MUST use exactly these 10 labeled lines」：STYLE、SHOT、CAMERA、COMPOSITION、SUBJECTS、STATIC_ACTION、PROPS、ENVIRONMENT、LIGHTING、MOOD；P2 只要保證欄位齊全 |
| 風格前綴由程式注入，LLM 不得改寫 | OpenDirector | `promptPrefix` 由程式從風格目錄覆寫（`recipe-normalize.ts`） |
| 影片 prompt 只寫運動，不重複首幀描述 | OpenDirector | 「Video prompts should focus on motion and animation, not repeating the image description」 |
| 最終剪輯核對素材來源是不是選定的組合 | LUNA 實戰 | 曾誤用測試檔 |
| 機位樹、VLM 從候選圖挑選記為 P6 以後參考 | ViMax | 機位樹：同機位共用首幀，長鏡不得直接接特寫；VLM：依角色一致、空間一致、與描述相符、無白邊黑邊比較 2 張候選。MV 場景變化多，完整機位樹可能過重，先記錄 |

## AutoMV 12 項評測準則

出處：arXiv 2512.12196 §4.1、Appendix B。分類結果：劇本層看得出的 5 項（Character Consistency、Physical Authenticity、Shot Continuity、Audio–Visual Correlation、Musical Theme Relevance）進 plan-critic 第 13 節；美學與節奏 6 項進 G1 rubric 當參考、不打分；Lip Sync 不適用（無對嘴）。理由：plan-critic 的邊界是「只找會讀錯、要人猜的地方」，美學準則放進來會讓必答題暴增（[g1-rubric.md](g1-rubric.md)）。
