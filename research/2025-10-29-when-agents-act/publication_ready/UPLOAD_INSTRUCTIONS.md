# Upload Instructions for Dataset Publication

This guide walks you through uploading the "When Agents Act" dataset to Kaggle and Hugging Face.

---

## 📦 What You're Publishing

**Dataset:** When Agents Act - LLM Ethical Decision-Making
**Size:** ~81 MB compressed, ~107 MB uncompressed
**Files:** 16 files (data + documentation)
**License:** CC0 1.0 (Public Domain)

---

## 🎯 Option 1: Kaggle

### Step 1: Prepare Account
1. Go to https://www.kaggle.com
2. Sign in (or create account)
3. Verify your account with phone number (required to publish datasets)

### Step 2: Create Dataset
1. Go to https://www.kaggle.com/datasets
2. Click **"New Dataset"** button (top right)
3. Click **"Select Files to Upload"**

### Step 3: Upload Files
**Select ALL files from this folder:**
```
✓ dilemmas.json
✓ judgements.json
✓ dilemmas_flat.csv
✓ judgements_flat.csv
✓ theory_action_paired.csv
✓ consensus_by_configuration.csv
✓ samples_reversals.csv
✓ difficulty_analysis.csv
✓ summary_by_condition.csv
✓ README.md                     ← Kaggle uses this as description
✓ CODEBOOK.md
✓ LICENSE.txt
✓ findings.md
✓ config.json
```

**Do NOT upload:**
- ❌ README_HF.md (this is for Hugging Face only)
- ❌ UPLOAD_INSTRUCTIONS.md (this file)

### Step 4: Fill Metadata
- **Title:** When Agents Act - LLM Ethical Decision-Making
- **Subtitle:** Theory-Action Gap in Frontier Language Models
- **Description:** Kaggle will auto-populate from README.md (you can edit if needed)
- **License:** Select **"CC0: Public Domain"**
- **Tags:** Add: `llm`, `ai-safety`, `ethics`, `benchmarking`, `gpt-5`, `claude`, `gemini`

### Step 5: Publish
1. Click **"Create"**
2. Dataset will go through validation (should take 1-2 minutes)
3. Once validated, it's live!

### Step 6: Post-Publication
- Share dataset URL (e.g., `kaggle.com/datasets/username/when-agents-act`)
- Optionally create a Kaggle notebook showcasing analysis
- Monitor discussion tab for questions

---

## 🤗 Option 2: Hugging Face

### Step 1: Prepare Account
1. Go to https://huggingface.co
2. Sign in (or create account)
3. Go to Settings → Access Tokens
4. Create a write token (needed for uploads)

### Step 2: Create Dataset Repository
1. Go to https://huggingface.co/new-dataset
2. **Owner:** Your username or organization
3. **Dataset name:** `when-agents-act`
4. **License:** Select **"CC0 1.0"**
5. Click **"Create dataset"**

### Step 3: Prepare Files
**IMPORTANT:** Rename README_HF.md to README.md before uploading

```bash
# In the publication_ready folder:
cp README_HF.md README.md
```

### Step 4: Upload Files (Web UI)
1. Click **"Files and versions"** tab
2. Click **"Add file"** → **"Upload files"**
3. Drag and drop ALL files:
```
✓ dilemmas.json
✓ judgements.json
✓ dilemmas_flat.csv
✓ judgements_flat.csv
✓ theory_action_paired.csv
✓ consensus_by_configuration.csv
✓ samples_reversals.csv
✓ difficulty_analysis.csv
✓ summary_by_condition.csv
✓ README.md                     ← Renamed from README_HF.md
✓ CODEBOOK.md
✓ LICENSE.txt
✓ findings.md
✓ config.json
```

4. Click **"Commit changes to main"**

### Alternative: Upload via Git (Advanced)
```bash
# Clone your new repo
git clone https://huggingface.co/datasets/YOUR_USERNAME/when-agents-act
cd when-agents-act

# Copy files
cp /path/to/publication_ready/* .
mv README_HF.md README.md

# Commit and push
git add .
git commit -m "Initial dataset upload"
git push
```

### Step 5: Verify Dataset Card
1. Go to your dataset page
2. Hugging Face will automatically render README.md with metadata
3. Check that:
   - Metadata tags appear (language, task, license)
   - Data preview works for CSV files
   - Download button works

### Step 6: Post-Publication
- Share dataset URL (e.g., `huggingface.co/datasets/username/when-agents-act`)
- Dataset card will have DOI for citations
- Optionally create a dataset viewer demo

---

## 📊 Data Verification Checklist

Before uploading, verify:

- [ ] All 14 data/doc files are present
- [ ] CSV files open correctly in Excel/pandas
- [ ] JSON files are valid (no syntax errors)
- [ ] README.md looks good in markdown preview
- [ ] LICENSE.txt is CC0 1.0
- [ ] Total size is under 100GB (you're at ~81MB ✓)

---

## 🔗 Cross-Linking (Post-Upload)

After publishing to both platforms:

1. **Update Kaggle dataset description:**
   - Add link to Hugging Face version
   - Add link to GitHub repo

2. **Update Hugging Face README:**
   - Add link to Kaggle version
   - Add link to GitHub repo

3. **Update GitHub repo (if applicable):**
   - Add badge/link to Kaggle dataset
   - Add badge/link to HF dataset

---

## 🎉 After Publishing

1. **Announce on social media:**
   - Twitter/X: "Just published 'When Agents Act' dataset..."
   - LinkedIn: Share with research context
   - Reddit: r/MachineLearning, r/LanguageModels

2. **Submit paper to arXiv:**
   - Use findings.md as basis
   - Link to datasets in paper

3. **Write blog post:**
   - Key findings summary
   - How to use the data
   - Link to datasets

---

## 💬 Questions?

- **Technical issues:** Check Kaggle/HF documentation
- **Dataset questions:** See CODEBOOK.md
- **Research questions:** See findings.md

---

## 📝 Citation

Once published, update README files with actual dataset URLs:

```bibtex
@dataset{when_agents_act_2025,
  title={When Agents Act: Behavioral Shifts in Large Language Model Ethical Decision-Making from Evaluation to Deployment},
  author={Claude (Anthropic) and Strakhov, George},
  year={2025},
  month={November},
  publisher={Kaggle},
  url={https://kaggle.com/datasets/YOUR_USERNAME/when-agents-act}
}
```

---

**Good luck with your publication! 🚀**
