# Property Scout 🏠

Automated property scraping system for real estate investment analysis. Currently supporting Idealista (Spain) with planned expansion to Zillow (USA), Rightmove (UK), and SeLoger (France).

## 🎯 Features

- **Automated Daily Scraping**: GitHub Actions workflow runs automatically every day at 9:00 AM UTC
- **Multi-Market Ready**: Modular architecture designed for easy expansion to new markets
- **Base44 Integration**: Automatically saves property data to your Base44 database
- **FREE Hosting**: Runs on GitHub Actions (2000 free minutes/month)
- **Anti-Bot Protection**: Uses Playwright browser automation to bypass detection
- **Property Analysis**: Extracts key metrics for investment decision-making

## 📊 Data Extracted

For each property, the scraper collects:
- Title and URL
- Price (€)
- Surface area (m²)
- Number of bedrooms
- Number of bathrooms
- Description
- Location (city, address)
- Rental potential estimate
- Source platform
- Date added

## 🚀 Quick Start

### Prerequisites

1. **GitHub Account** (free)
2. **Base44 Account** with API credentials
3. **Base44 App** with a table named `BienImmobilier`

### Setup Instructions

#### 1. Configure GitHub Secrets

Navigate to your repository settings:
- Go to `Settings` → `Secrets and variables` → `Actions`
- Click `New repository secret`
- Add two secrets:
  - `BASE44_API_KEY`: Your Base44 API key
  - `BASE44_APP_ID`: Your Base44 app ID

#### 2. Manual Test Run

- Go to `Actions` tab in your repository
- Select `Daily Idealista Scraper` workflow
- Click `Run workflow` → `Run workflow`
- Monitor the execution in real-time

#### 3. Verify Data

Check your Base44 app to see the scraped properties appearing in the `BienImmobilier` table.

## ⚙️ Configuration

### Modify Scraping Parameters

Edit `.github/workflows/daily-scrape.yml`:

```yaml
- name: Run Idealista scraper
  run: |
    python scrape_idealista.py --city madrid --operation venta --pages 2
```

**Parameters:**
- `--city`: City to scrape (default: `madrid`)
- `--operation`: `venta` (sale) or `alquiler` (rent)
- `--pages`: Number of pages to scrape (default: `1`)

### Change Schedule

Modify the cron expression in `.github/workflows/daily-scrape.yml`:

```yaml
schedule:
  - cron: '0 9 * * *'  # Every day at 9:00 AM UTC
```

[Crontab Guru](https://crontab.guru/) can help you create custom schedules.

## 📁 Project Structure

```
property-scout/
├── scrape_idealista.py       # Main scraper script
├── requirements.txt          # Python dependencies
├── .github/
│   └── workflows/
│       └── daily-scrape.yml  # GitHub Actions automation
└── README.md                 # This file
```

## 🔧 Local Development

### Installation

```bash
# Clone the repository
git clone https://github.com/capitalsuccesshub-maker/property-scout.git
cd property-scout

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Set environment variables
export BASE44_API_KEY="your_api_key"
export BASE44_APP_ID="your_app_id"
```

### Run Locally

```bash
# Dry run (scrape without sending to Base44)
python scrape_idealista.py --city madrid --operation venta --pages 1 --dry-run

# Full run
python scrape_idealista.py --city madrid --operation venta --pages 2
```

## 🌍 Roadmap

- [x] Idealista (Spain) scraper
- [x] Base44 integration
- [x] GitHub Actions automation
- [ ] Zillow (USA) scraper
- [ ] Rightmove (UK) scraper
- [ ] SeLoger (France) scraper
- [ ] Investment scoring algorithm
- [ ] Email notifications
- [ ] Multi-city support

## 💰 Cost

**100% FREE** 🎉

- GitHub Actions: 2000 minutes/month (free tier)
- Estimated usage: ~10 minutes/day = 300 minutes/month
- Base44: Free tier available

## 🤝 Contributing

This is a private project for investment purposes. To add support for new markets:

1. Create a new scraper file (e.g., `scrape_zillow.py`)
2. Follow the same structure as `scrape_idealista.py`
3. Update the workflow to include the new scraper

## 📝 License

Private - All Rights Reserved

## ⚠️ Disclaimer

This tool is for personal investment research only. Always respect website terms of service and robots.txt files. Use responsibly and ethically.

---

**Built with ❤️ for real estate investors**
