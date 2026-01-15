# ❓ Frequently Asked Questions (FAQ)

## General Questions

### What is SentinelScope Pro?
SentinelScope Pro is an AI-powered SaaS platform that automates construction compliance auditing for NYC general contractors. It analyzes site photos to detect compliance gaps, integrates with NYC DOB data for real-time violation tracking, and generates audit-ready reports.

### Who is this tool for?
- **Primary Users:** NYC General Contractors managing multiple construction projects
- **Secondary Users:** Construction managers, safety officers, and compliance teams
- **Project Sizes:** Best suited for firms managing 5-20+ projects simultaneously

### How much does it cost?
- **Development/Testing:** Free (using Streamlit Cloud free tier + free API tiers)
- **Starter Plan:** $500/month (5 projects, 50 audits/month)
- **Professional Plan:** $2,500/month (unlimited projects and audits)
- **Enterprise:** Custom pricing for 100+ projects

### What's the ROI?
For a mid-size GC firm managing 10 active projects:
- **Manual Cost:** $50,000/year ($5,000 per audit × 10 projects)
- **SentinelScope Cost:** $6,240/year ($500/month + API fees)
- **Savings:** $43,760/year (87% cost reduction)
- **Time Saved:** 40-80 hours → 10 minutes per audit

---

## Technical Questions

### What technologies does SentinelScope use?
- **Frontend:** Streamlit (Python web framework)
- **AI Model:** DeepSeek-V3 Vision API (cost-effective alternative to GPT-4V)
- **Database:** Supabase (PostgreSQL with real-time sync)
- **APIs:** NYC DOB Open Data API, Geopy geocoding
- **Export:** FPDF2 for PDF generation, JSON/CSV for data export

### Why DeepSeek instead of OpenAI?
- **Cost:** 97% cheaper ($0.14/1M tokens vs $5/1M)
- **Speed:** Faster inference times for batch processing
- **Accuracy:** Comparable performance on construction milestone classification
- **Practical Impact:** 10,000 images = $14 (DeepSeek) vs $500 (OpenAI)

### Do I need coding experience to use it?
No! SentinelScope has a user-friendly web interface built with Streamlit. Simply:
1. Upload site photos (drag-and-drop)
2. Enter project details
3. Click "Analyze"
4. Download PDF report

### Can I self-host it?
Yes! The codebase is open source. You can:
- Deploy to your own Streamlit Cloud account
- Host on AWS/GCP/Azure with Docker
- Run locally on your machine for development

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

### What data does SentinelScope store?
- **Project metadata:** Name, address, type, date
- **Audit results:** Detected milestones, compliance gaps, risk scores
- **User information:** Email, name, team assignments (if using authentication)
- **What we DON'T store:** Original site photos (processed in memory, not saved)

All data is stored in Supabase with row-level security for multi-tenant isolation.

---

## Usage Questions

### What types of photos should I upload?
**Best Results:**
- ✅ Clear, well-lit site captures
- ✅ Multiple angles of each construction phase
- ✅ Close-ups of specific systems (foundation, MEP, fireproofing)
- ✅ Wide shots showing overall progress

**Avoid:**
- ❌ Blurry or dark photos
- ❌ Photos of plans/drawings (use actual site captures)
- ❌ Photos with people blocking critical features

### How many photos do I need?
- **Minimum:** 10-15 photos for basic audit
- **Recommended:** 30-50 photos for comprehensive coverage
- **Enterprise:** 100+ photos for detailed forensic analysis

More photos = better accuracy and stronger compliance evidence.

### What project types are supported?
- Commercial buildings (office, retail, mixed-use)
- Residential (single-family, multi-family)
- Industrial (warehouses, manufacturing)
- Institutional (schools, hospitals)

The AI is trained on NYC Building Code milestones specific to each type.

### How accurate is the AI classification?
- **Overall Accuracy:** 94%+ on milestone detection
- **Fuzzy Matching:** 85%+ accuracy using RapidFuzz algorithm
- **Human Review:** Always recommended for critical compliance decisions

The system provides confidence scores with each classification so you can review low-confidence results.

### Can I edit the AI's findings?
Yes! The system allows you to:
- Review and override AI classifications
- Add manual notes to each gap
- Mark false positives
- Export both AI and human-reviewed results

---

## Compliance Questions

### What building codes does it cover?
- **NYC Building Code 2022** (primary)
- **NYC Building Code 2025** (in progress)
- Support for LA, Chicago, Boston codes coming in Q3 2025

### Does it replace a licensed professional?
No! SentinelScope is a **productivity tool**, not a replacement for:
- Licensed architects
- Professional engineers
- NYC DOB inspectors
- Insurance underwriters

Always have a licensed professional review critical compliance decisions.

### Can I use the reports for insurance audits?
Yes! The PDF reports include:
- Legal timestamps
- Confidence scores
- NYC Building Code references
- Visual evidence tables
- Risk assessments

Many GCs use these reports as **supporting documentation** for insurance renewals, but check with your carrier for specific requirements.

### How does it integrate with NYC DOB data?
SentinelScope connects to the NYC Open Data API to:
- Pull real-time violation data by BBL (Borough-Block-Lot)
- Track DOB complaint history
- Monitor inspection deadlines
- Alert on new violations

This requires no special permissions—the API is publicly accessible.

---

## Troubleshooting

### The AI isn't detecting milestones correctly. What should I do?
1. **Check Photo Quality:** Ensure images are clear and well-lit
2. **Upload More Photos:** More context helps the AI understand project phase
3. **Verify Project Type:** Make sure you selected the correct building type
4. **Manual Override:** You can always manually classify milestones

### I'm getting API errors. How do I fix this?
**DeepSeek API Errors:**
- Verify your API key is valid at https://platform.deepseek.com
- Check your API quota (free tier: 10M tokens/month)
- Ensure you have internet connectivity

**Supabase Errors:**
- Confirm your `SUPABASE_URL` and `SUPABASE_KEY` are correct
- Check if your Supabase project is paused (free tier auto-pauses after inactivity)
- Verify your database schema matches the expected structure

### The app is slow. How can I speed it up?
- **Use Batch Processing:** Process multiple images at once (60% faster)
- **Upgrade API Tier:** Free tiers have rate limits
- **Optimize Photos:** Resize large images before upload (max 2MB recommended)
- **Self-Host:** Deploy to a dedicated server for better performance

### Can I run this offline?
Partially. You can:
- ✅ Run the Streamlit UI locally
- ✅ Use local database for data storage
- ❌ AI classification requires internet (DeepSeek API)
- ❌ NYC DOB data requires internet (Socrata API)

For true offline mode, you'd need to:
1. Deploy a local AI model (e.g., LLaVA, InternVL)
2. Download NYC DOB data as static files
3. Use SQLite instead of Supabase

---

## Pricing & Billing

### Is there a free trial?
Yes! You can:
- Use the live demo at [sentinelscope.streamlit.app](https://sentinelscope.streamlit.app)
- Deploy your own instance on Streamlit Cloud (free tier)
- Run locally with your own API keys

### What are the API costs?
**DeepSeek API:**
- Free tier: 10M tokens/month
- Paid: $0.14/1M input tokens, $0.28/1M output tokens
- Typical audit: $0.50-$2.00 depending on photo count

**Supabase:**
- Free tier: 500MB database, 2GB bandwidth
- Pro: $25/month for 8GB database, 250GB bandwidth

**NYC Open Data API:**
- Free for 1,000 requests/day
- Free unlimited with app token

### Can I cancel anytime?
Yes! There are no long-term contracts. Cancel anytime and retain access until the end of your billing period.

---

## Support & Community

### How do I get help?
- **Documentation:** Check this FAQ and other docs in `/docs`
- **GitHub Issues:** Report bugs at [github.com/NickAiNYC/Sentinel-Scope/issues](https://github.com/NickAiNYC/Sentinel-Scope/issues)
- **Email:** nick@thrivai.ai
- **Community:** Join our Slack channel (link in README)

### Can I contribute to the project?
Absolutely! See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Coding standards
- Pull request process
- Feature request guidelines

### Is there enterprise support?
Yes! Enterprise customers receive:
- Dedicated account manager
- Priority support (4-hour SLA)
- Custom feature development
- On-premise deployment assistance
- Training sessions for your team

Contact nick@thrivai.ai for enterprise inquiries.

---

## Roadmap & Future Features

### What's coming next?
**Q1 2025:**
- User authentication and team management
- Mobile app (iOS/Android)
- Email notification system

**Q2 2025:**
- OpenSpace API integration
- Slack/Teams notifications
- Advanced analytics dashboard

**Q3 2025:**
- Multi-city support (LA, Chicago, Boston)
- OSHA safety compliance checks
- OCR for permit/badge extraction

See the [Roadmap section in README](../README.md#-roadmap) for details.

### Can I request features?
Yes! Open a GitHub issue with the `feature-request` label. Popular requests get prioritized.

---

## Security & Privacy

### Is my data secure?
Yes! SentinelScope uses:
- **Supabase Row-Level Security:** Multi-tenant data isolation
- **HTTPS encryption:** All data transmitted securely
- **No photo storage:** Images processed in memory, not saved
- **Environment variables:** Secrets never hardcoded in code

### Who can see my data?
- **You and your team:** Only users in your organization
- **Supabase:** Encrypted at rest, access logged
- **AI APIs:** Photos sent to DeepSeek for classification (not stored by them)
- **NYC Open Data:** Public violation data only

### Is this GDPR compliant?
The codebase is designed with privacy in mind:
- User data can be deleted on request
- Minimal personal information collected
- Clear data retention policies

For full GDPR compliance in production, consult with a legal team.

---

## License & Legal

### What license is SentinelScope under?
**MIT License** - You can:
- ✅ Use commercially
- ✅ Modify and distribute
- ✅ Use privately
- ✅ Sublicense

See [LICENSE](../LICENSE) for full terms.

### Can I use this for my own product?
Yes! The MIT license allows commercial use. However:
- Give attribution to the original project
- Don't claim it as entirely your own work
- Follow the license terms

### Are there any usage restrictions?
No restrictions! Just don't:
- Remove copyright notices
- Hold the authors liable for issues
- Claim the software is officially endorsed by NYC DOB

---

**Still have questions?** Open an issue on GitHub or email nick@thrivai.ai.
