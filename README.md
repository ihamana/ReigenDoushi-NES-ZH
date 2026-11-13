# 靈幻道士 中文化（Reigen Doushi, FC）

紅白機（Famicom）遊戲《霊幻道士》的**繁體中文／簡體中文雙語**中文化修補程式。
一個 ROM 內含繁中與簡中，在標題選單用 **Select** 切換語言。

> 本專案**不包含遊戲 ROM**，也不收錄遊戲的日文原文。請使用你自己合法擁有的原版 ROM 建置。

## 特色

- 全部對話、門口說明、選單、取名／密碼畫面按鈕中文化（縫合像素 12px 字型）
- 繁中／簡中雙語：標題選單第三行「繁中　简中」，按 Select 切換
- 調查房屋時出現師父頭像、門口對話出現弟子頭像（頭像圖片需自備，見下方）
- 標題畫面輸入「上上下下左右左右」：得到全道具、古法書 99 本、村莊走路兩倍速
- 道士之心輸入「どうしのこころどうしのこころへ」直接到洛黃村
- 容量由 256KB 擴充到 512KB（MMC1 SUROM）

## 建置

### 需要

- Python 3.8 以上（Windows 安裝時請勾選「Add python.exe to PATH」）
- 原版 ROM：No-Intro「**Reigen Doushi (Japan).nes**」
  - 含檔頭 CRC32 `8F0EAB04`（不含檔頭的 PRG CRC32 `0021ED29`）

### Windows

把原版 ROM **拖到 `build.bat` 上**即可。第一次會自動安裝需要的套件（Pillow、openpyxl）。
完成後檔案在 `out\Reigen_Doushi_(CHT_CHS)_V2.6.nes`。

### 命令列（Windows / macOS / Linux）

```
pip install -r requirements.txt
python build.py "Reigen Doushi (Japan).nes"
```

| 參數 | 說明 |
|---|---|
| `輸出.nes` | 第二個參數，指定輸出檔（預設 `out/Reigen_Doushi_(CHT_CHS)_V2.6.nes`） |
| `--ips` | 另外輸出 `.ips`（以原版 ROM 為基底） |
| `--text 檔案.xlsx` | 改用其他翻譯試算表 |
| `--portrait 資料夾` | 改用其他頭像資料夾 |

建置程式會先檢查 ROM 的 CRC32，不符時會停止。

## 頭像（自備）

原作者版本的頭像取自電影劇照，有著作權與肖像權問題，所以**不附在本專案裡**。
沒有提供時會用「道長」「文才」字樣的預設圖，遊戲功能不受影響。

想放自己的圖片：

```
python tools/portrait_tool.py master   你的圖片.jpg   # 師父：48×64 像素
python tools/portrait_tool.py disciple 你的圖片.png   # 弟子：32×32 像素
python build.py "Reigen Doushi (Japan).nes"
```

規格與細節見 [`assets/portrait/README.md`](assets/portrait/README.md)。

## 修改翻譯

翻譯在 `text/靈幻道士_翻譯.xlsx`，改「中文翻譯」欄後重新建置即可。

| 分頁 | 內容 |
|---|---|
| 對話 | 遊戲對話。「日文結尾換行數」由建置程式用來對齊選項位置，請勿修改 |
| 門口說明 | 調查門口時的說明（最多 2 行，每行最多 5 字） |
| 選單與介面 | 選單、取名／密碼畫面的標籤 |
| 編碼表 | 原版遊戲的文字編碼 |

- 對話框每行最多 9 個中文字，過長會自動斷行；`<等待>` 等按鍵、`<換頁>` 強制換頁。
- 簡體版由繁體**逐字**自動轉換（`src/t2s_map.json`），繁簡共用同一套字碼。
- 如果你手邊有含日文原文的完整試算表，可用 `python tools/strip_jp.py 完整版.xlsx text/靈幻道士_翻譯.xlsx` 轉成公開版。

## 專案結構

```
build.py              一鍵建置（檢查 ROM → 修補 → 輸出 .nes／.ips）
build.bat / build.sh  Windows／macOS・Linux 啟動檔
src/
  patch.py            主要修補流程（文字重排、字形、選單、頭像、各項修正）
  engine2.s           6502 文字引擎（12×12 字形、繁簡切換、頭像顯示）
  menus.py            標題選單、取名／密碼畫面中文標籤
  asm.py, dis6502.py  簡易 6502 組譯器
  pixfont.py          BDF 點陣字型讀取
  zhconv.py           繁→簡逐字轉換（t2s_map.json）
  portrait.py         頭像圖片 → NES 圖塊
  layout.py           對話斷行
  village_tiles.json  各村莊未使用的圖塊（頭像暫存用）
text/                 翻譯試算表
fonts/                縫合像素字型（OFL 1.1）
tools/                頭像轉換、試算表轉換、IPS 產生
assets/portrait/      自備頭像放這裡（不提交）
```

## 授權

| 內容 | 授權 |
|---|---|
| 本專案的程式碼、組合語言、翻譯文本與文件 | [CC BY-NC-SA 4.0](LICENSE)（姓名標示－非商業性－相同方式分享）© 2026 MANA |
| 縫合像素字型（`fonts/*.bdf`） | [SIL Open Font License 1.1](fonts/OFL.txt) © TakWolf |
| 《霊幻道士》遊戲本體（程式、圖像、音樂、日文原文） | 屬原權利人所有，**本專案不包含** |

- 本專案只提供修補程式與翻譯，不提供、也請勿散布遊戲 ROM 或修補後的 ROM。
- 字型依 OFL 1.1 原樣隨附；CC BY-NC-SA 4.0 不適用於字型檔。
- 頭像圖片不附，請只使用你有權使用的圖片。

## 版本紀錄

**V2.6**
- 修正使用密技後，帶出房間的小殭屍在村莊不會跟著走的問題（同時修正原版距離只比低位元組的缺陷）
- 武道館問答 #201 正解改為「棺材」

**V2.5**
- 修正武道館問答 #212 選項錯位
- 武道館問答 #202 正解改為「在胸口打木樁」、#209 改為「中國日報」、#212 譯文改為「溥儀」

**V2.3**
- 語言改用 Select 切換，選中的語言前顯示 ●；「簡中」改為「简中」；游標對準文字中間

**V2.2**
- 繁體、簡體合併為同一個 ROM，標題選單加入語言選項

**V2.1**
- 修正頭像顯示期間背景（欄杆）變樣的問題（洛黃村等）

**V2.0**
- 字型改用縫合像素 12px；加入簡體版

**V1.0**
- 繁體中文化；加入師父／弟子頭像；標題密技；容量擴充到 512KB（MMC1 SUROM）

## 致謝

- 中文化：MANA
- 字型：[縫合像素字型 Fusion Pixel Font](https://github.com/TakWolf/fusion-pixel-font)（TakWolf，OFL 1.1）
