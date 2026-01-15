# ⚠️ Important: Manual Cleanup Required

## Security Alert - Exposed API Keys

During the repository cleanup, we discovered that sensitive credentials were committed to git history. While these files are now in `.gitignore`, they still exist in past commits.

### Files Containing Secrets (in git history)

1. `.env.txt` - Contains DeepSeek API key
2. `secret.toml` - Contains DeepSeek API key  
3. `.streamlit:secrets.toml` - Contains DeepSeek API key, Supabase credentials
4. `.streamlit/secrets.toml` - Contains DeepSeek API key

### Exposed Credentials

**DeepSeek API Keys:**
- `sk-a9aac9ad3db44e42bebf87314c1b0896`
- `sk-555051006a4740198a32c8f16b27ab62`

**Supabase:**
- URL: `https://sdbjypczhfyzzygzmvzq.supabase.co`
- Anon Key: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (full key in files)

---

## Required Actions

### 1. Rotate All API Keys (URGENT)

**DeepSeek:**
1. Go to https://platform.deepseek.com
2. Delete the exposed API keys
3. Generate new API keys
4. Update your local `.streamlit/secrets.toml` file (never commit!)

**Supabase:**
1. Go to your Supabase project dashboard
2. Navigate to Project Settings → API
3. Consider rotating the service key if exposed
4. Update your local `.streamlit/secrets.toml` file

### 2. Remove Files from Git History

These files are now gitignored, but remain in history. To remove them:

```bash
# Option 1: Using git-filter-repo (recommended)
pip install git-filter-repo

git filter-repo --path .env.txt --invert-paths
git filter-repo --path secret.toml --invert-paths  
git filter-repo --path .streamlit:secrets.toml --invert-paths

# Then force push (WARNING: rewrites history)
git push origin --force --all
git push origin --force --tags
```

```bash
# Option 2: Using BFG Repo-Cleaner (alternative)
# Download from: https://rtyley.github.io/bfg-repo-cleaner/

java -jar bfg.jar --delete-files .env.txt
java -jar bfg.jar --delete-files secret.toml
java -jar bfg.jar --delete-files '.streamlit:secrets.toml'

git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push origin --force --all
```

**⚠️ Warning:** Force pushing rewrites history. Coordinate with team members!

### 3. Delete Extraneous Files

```bash
# Remove unusual secrets file with colon in name
rm .streamlit:secrets.toml

# Remove deprecated files
rm .env.txt
rm secret.toml

# Remove empty directory
rmdir sentinel-scope/

# Commit the cleanup
git add -A
git commit -m "Remove extraneous and deprecated files"
git push
```

### 4. Set Up Secrets Properly

**For local development:**
```bash
# Copy the example file
cp .env.example .env

# Edit with your NEW API keys (never commit this file!)
nano .env

# Or use Streamlit secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
nano .streamlit/secrets.toml
```

**For production (Streamlit Cloud):**
1. Go to https://share.streamlit.io
2. Select your app
3. Click Settings → Secrets
4. Paste your secrets in TOML format
5. Save

---

## Best Practices Going Forward

### Never Commit Secrets

✅ **DO:**
- Use `.env` files (with `.gitignore`)
- Use environment variables
- Use secrets management services (AWS Secrets Manager, etc.)
- Use `.env.example` templates (without real values)

❌ **DON'T:**
- Commit files with actual API keys
- Put secrets in source code
- Share secrets in PR descriptions
- Store secrets in documentation

### Pre-commit Hook

Add this pre-commit hook to catch secrets before committing:

```bash
# .git/hooks/pre-commit
#!/bin/bash

# Check for potential secrets
if git diff --cached | grep -E '(api_key|API_KEY|secret|password|token).*=.*[a-zA-Z0-9]{20,}'; then
    echo "⚠️  WARNING: Possible secret detected in staged changes!"
    echo "Please review and remove before committing."
    exit 1
fi
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

---

## Additional Cleanup Items

### Files to Review/Remove

1. **`tests/test_dob_engine`** (577 bytes)
   - Appears to be misnamed (should be `.py` extension)
   - Review and rename or delete:
   ```bash
   cat tests/test_dob_engine  # Check contents
   # If it's test code:
   mv tests/test_dob_engine tests/test_dob_engine.py
   # If it's garbage:
   rm tests/test_dob_engine
   ```

### Tests Need Updating

The tests in `tests/test_gap_detector.py` are failing because the API signature changed:

```
TypeError: ComplianceGapEngine.detect_gaps() missing 1 required positional argument: 'api_key'
```

**To fix:**
1. Update test fixtures to include mock API keys
2. Use `pytest-mock` to mock API calls
3. Separate unit tests (mocked) from integration tests (real API)

Example fix:
```python
@pytest.fixture
def mock_api_key():
    return "test_api_key_mock"

def test_detect_gaps_partial_completion(structural_engine, mock_api_key):
    found_milestones = ["Foundation"]
    result = structural_engine.detect_gaps(found_milestones, mock_api_key)
    # ... rest of test
```

---

## Summary

**Completed:**
- ✅ Updated `.gitignore`
- ✅ Created template files
- ✅ Applied code formatting
- ✅ Enhanced documentation

**Manual Actions Required:**
- ⚠️ Rotate exposed API keys
- ⚠️ Remove secrets from git history
- ⚠️ Delete extraneous files
- ⚠️ Update tests
- ⚠️ Review and fix `test_dob_engine` file

---

**Need Help?** 
- See [CLEANUP_SUMMARY.md](CLEANUP_SUMMARY.md) for full details
- Email: nick@thrivai.ai
- GitHub Issues: https://github.com/NickAiNYC/Sentinel-Scope/issues

**Remember:** Security is not just about code—it's about process. Always review what you're committing!
