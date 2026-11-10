# 線上文件同步

## 原則

1. **正本是 YAML。** 線上文件與 `docs/mv_plan.md` 都是 `render_plan.py` 的產物，不從文件反推 YAML。
2. 要改內容就改 YAML、跑 lint、重新 render，再同步。使用者在文件上留的意見由 Claude 轉成 YAML 修改。
3. **只替換變動的區塊，不整份重貼。** 線上文件的版面可能經過手動排版（表格欄寬、標題順序、補充說明），整份重貼會洗掉。
4. 同步前先 render，用 render 結果當「新內容」，只拿變動的部分去換。

## 沒有線上文件

只輸出 `docs/mv_plan.md`：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/mv-script/scripts/render_plan.py --plan plan --out docs/mv_plan.md
```

- 欄位的中文名稱讀 `plan/labels.yaml`（沒有就顯示原 key；範本在 `templates/labels.yaml`）。`labels.yaml` 的 `realize:` 可以覆蓋「做法」的中文名稱；`texts.generated_note`、`texts.proposed_note` 可以改產物檔頭的說明文字。
- 這個檔案提交進 git，但標明「產物，不手改」（render 會在檔頭寫）。
- 使用者要線上文件時，再依下面流程建立，並把 id 寫進 `project.yaml`。

## 有線上文件

### 記錄 id

文件 id 與內容區的 body node id 記在 `project.yaml`：

```yaml
docs:
  online_doc_id: <文件 id>
  body_node_id: <內容區 node id>
  output_md: docs/mv_plan.md
```

- 換工作階段或換電腦時，靠這兩個 id 找到文件；不要寫在對話記憶裡。
- 找不到文件（被刪、被改版）就問使用者，不要新建一份取代。

### render 的段落對應

`render_plan.py` 產生的 Markdown 有固定的二級標題，同步時以標題為單位對應：

| 標題 | 來源 | 變動時機 |
| --- | --- | --- |
| 參數與已確認決定 | `project.yaml` 的 `params`、`decisions` | 使用者回答新決定後 |
| 故事 | `story.yaml` | 寫完或改完某段劇情 |
| 名詞表 | `glossary.yaml` 的 entities | 新增或修改實體 |
| 詞彙 | `glossary.yaml` 的 vocab | 很少變 |
| 鏡頭 | `shots.yaml` | 每寫完一段、每次審稿修改 |
| 待回答的問題 | `proposed`、`questions`、review 的 `open` | 每次 |

### 替換步驟

1. 讀線上文件目前的內容（用該文件工具的讀取功能），找出要換的區塊。
2. 比對 render 結果，列出變動的單位：
   - 鏡頭：以鏡頭 id（`s012`）為單位，一鏡一個區塊或一列。
   - 實體：以實體名稱為單位。
   - 決定：新增的列。
3. 只替換這些單位。新增的鏡頭插在相鄰鏡頭之後；刪除的鏡頭整塊移除。
4. 「待回答的問題」整段重換（它是衍生內容，沒有手動排版價值）。
5. 同步後讀回確認：變動的區塊是新內容，沒變的區塊沒被動到。
6. 在對話裡告訴使用者換了哪些鏡頭與實體，附文件連結。

### 注意

- 不要把整份 `mv_plan.md` 貼進文件內容區。
- 不要刪使用者在文件裡加的批註或留言；有留言先處理再換。
- 文件工具的細節（node 結構、更新操作）以該工具的說明為準；本外掛只規定「替換變動的單位」這個原則。
- 一整個大段落（Build 以後一次寫完）累積了很多變動時，可以一次同步，但仍然逐單位替換。

## 什麼時候同步

| 時機 | 同步 |
| --- | --- |
| 一段 shots 寫完、lint 與審稿處理完、render 後 | 是（給使用者確認用） |
| 使用者確認、commit 之前 | 把 `confirmed` 狀態同步 |
| 自行完成模式 | 每段 commit，但線上文件可在全片結束時一次同步（需告知使用者） |
| 只改了 YAML 的註解或空白 | 否 |
