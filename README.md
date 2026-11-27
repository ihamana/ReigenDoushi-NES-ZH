# 靈幻道士 中文化（Reigen Doushi, FC）

紅白機（Famicom）遊戲《霊幻道士》的**繁體中文／簡體中文雙語**中文化修補程式。
一個 ROM 內含繁中與簡中，在標題選單用 **Select** 切換語言。

> 本專案**不包含遊戲 ROM**，請使用你自己合法擁有的原版 ROM 建置。翻譯試算表附有日文原文對照。

## 特色

- 全部對話、門口說明、選單、取名／密碼畫面按鈕中文化（縫合像素 12px 字型）
- 繁中／簡中雙語：標題選單第三行「繁中　简中」，按 Select 切換
- 調查房屋時出現道長頭像、門口對話出現文才頭像
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
| `--ips` | 另外輸出 `.ips` 修補檔 |
| `--bps` | 另外輸出 `.bps` 修補檔 |
| `--text 檔案.xlsx` | 改用其他翻譯試算表 |

建置程式會先檢查 ROM 的 CRC32，不符時會停止。

## 現成修補檔

`release/` 內有：

| 檔案 | 說明 |
|---|---|
| `Reigen_Doushi_CHT_CHS_V2.6.ips` | 修補檔，用 Lunar IPS、Floating IPS、Rom Patcher JS 等套用到原版 ROM |
| `Reigen_Doushi_HDPack_V2.6.zip` | Mesen HD Pack（見下方） |

套用後的 ROM：CRC32 `6BD1CAFC`（含檔頭）／`2F4A2156`（不含檔頭）。自己建置的結果與此完全相同。

## Mesen HD Pack（高解析文字）

`release/Reigen_Doushi_HDPack_V2.6.zip` 是給 Mesen 用的高解析文字包，把遊戲中的文字換成 4 倍解析度的思源宋體（Source Han Serif）。

- 全部中文文字（對話、門口說明、標題選單、取名／密碼畫面按鈕、玩家名字），繁中用繁體字形、简中用簡體字形
- 取名／密碼畫面的假名、標題畫面英文字、游標
- 最上方狀態欄（村名、古法書數量、物品）維持原版圖案

安裝（Mesen 2）：
1. 解壓到 Mesen 的 `HdPacks` 資料夾，資料夾名稱改成和 ROM 檔名（不含 `.nes`）相同，例如 `HdPacks\Reigen_Doushi_CHT_CHS_V2.6\hires.txt`。
2. Mesen 設定 → 影像 → 勾選「使用 HD Pack」，重新載入遊戲。

## 修改翻譯

翻譯在 `text/靈幻道士_翻譯.xlsx`，改「中文翻譯」欄後重新建置即可。

| 分頁 | 內容 |
|---|---|
| 對話 | 遊戲對話（日文原文／中文翻譯對照）。建置時會依日文原文的結尾換行數對齊選項位置，請勿修改「日文原文」欄 |
| 門口說明 | 調查門口時的說明（日文原文／中文翻譯對照；最多 2 行，每行最多 5 字） |
| 選單與介面 | 選單、取名／密碼畫面的標籤 |
| 編碼表 | 原版遊戲的文字編碼 |

- 對話框每行最多 9 個中文字，過長會自動斷行；`<等待>` 等按鍵、`<換頁>` 強制換頁。
- 簡體版由繁體**逐字**自動轉換（`src/t2s_map.json`），繁簡共用同一套字碼。

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
tools/                試算表轉換、IPS／BPS 產生
assets/portrait/      道長、文才頭像圖片
release/              現成的 IPS 修補檔與 Mesen HD Pack
```

## 授權

| 內容 | 授權 |
|---|---|
| 本專案的程式碼、組合語言、翻譯文本與文件 | [CC BY-NC-SA 4.0](LICENSE)（姓名標示－非商業性－相同方式分享）© 2026 [MANA](https://www.facebook.com/ManaYi520) |
| 縫合像素字型（`fonts/*.bdf`） | [SIL Open Font License 1.1](fonts/OFL.txt) © TakWolf |
| HD Pack 內的字形圖（思源宋體） | SIL Open Font License 1.1 © Adobe |
| 《霊幻道士》遊戲本體（程式、圖像、音樂、日文原文） | 屬原權利人所有；本專案不包含 ROM，翻譯試算表中的日文原文僅供翻譯對照 |

- 本專案只提供修補程式與翻譯，不提供、也請勿散布遊戲 ROM 或修補後的 ROM。
- 字型依 OFL 1.1 原樣隨附；CC BY-NC-SA 4.0 不適用於字型檔。

## 版本紀錄

**V2.6**
- 新增 Mesen HD Pack（思源宋體高解析文字）
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

- 中文化：[MANA](https://www.facebook.com/ManaYi520)
- 字型：[縫合像素字型 Fusion Pixel Font](https://github.com/TakWolf/fusion-pixel-font)（TakWolf，OFL 1.1）
- HD Pack 字型：思源宋體 Source Han Serif（Adobe，OFL 1.1；以同字形的 Noto Serif CJK 繪製）
