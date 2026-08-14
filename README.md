# Chris Moody Stock Scanner (Automated GitHub Actions Edition)

Automated dual-screener stock momentum scanner powered by TradingView data and GitHub Actions.

## 📁 Repository Structure

```
.
├── .github/workflows/
│   └── daily_scan.yml                    # Automated GitHub Actions workflow (runs Mon-Fri)
├── Screener_1_With_Dollar1_Move/         # Screener 1: Enforces >= $1.00 move from Open
│   ├── Chris_Moody_Daily_Scans/          # Daily Excel scan files
│   └── Chris_Moody_Watchlists/           # Watchlists & TradingView .txt exports
├── Screener_2_No_Dollar1_Limit/          # Screener 2: No $1.00 move constraint (All gainers)
│   ├── Chris_Moody_Daily_Scans/          # Daily Excel scan files
│   └── Chris_Moody_Watchlists/           # Watchlists & TradingView .txt exports
├── chris_moody_scanner.py                # Timezone-aware Python scanner script
├── requirements.txt                      # Dependencies list
└── README.md                             # Documentation & Setup Guide
```

---

## 🚀 Step-by-Step Setup Guide (2 Minutes)

### Step 1: Create a New Repository on GitHub
1. Open your browser where your GitHub account is signed in and go to: **[github.com/new](https://github.com/new)**
2. In the **Repository name** box, type: `chris-moody-stock-scanner`
3. Leave it as **Public** (or **Private**).
4. **Do NOT** check "Add a README file" (since we already created one).
5. Click the green **Create repository** button.

### Step 2: Upload Your Desktop Folder Files
1. On the page that appears, click the link: **`uploading an existing file`** (or click **Add file** -> **Upload files**).
2. Open your Desktop folder: [`C:\Users\DELL\Desktop\Chris_Moody_Stock_Scanner`](file:///C:/Users/DELL/Desktop/Chris_Moody_Stock_Scanner)
3. Select **all files and folders** inside `Chris_Moody_Stock_Scanner` and drag them into the GitHub upload area.
4. Click the green **Commit changes** button.

### Step 3: Enable Write Permissions (Required for Auto-Updates)
1. Go to your repository on GitHub -> Click **Settings** tab.
2. In the left menu, select **Actions** -> **General**.
3. Scroll down to **Workflow permissions**.
4. Select **Read and write permissions**.
5. Check **Allow GitHub Actions to create and approve pull requests**.
6. Click **Save**.

---

## ⚡ How to Run It Manually Anytime (1-Click)

1. Click the **Actions** tab at the top of your GitHub repository.
2. Click **Daily Chris Moody Stock Scanner** on the left menu.
3. Click **Run workflow** -> green **Run workflow** button.
4. GitHub Actions will run in the cloud and automatically update your watchlists!
