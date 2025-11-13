# Installation Guide - Word to Elementor Converter

Professional Document Conversion Tool - Version 3.0

---

## System Requirements

### Operating System
- Windows 10/11
- macOS 10.14+
- Linux (Ubuntu 20.04+, CentOS 8+)

### Software Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Web browser (Chrome, Firefox, Safari, or Edge)

### WordPress Requirements
- WordPress 5.0+
- Elementor plugin (Free or Pro)
- PHP 7.4+
- MySQL 5.6+

---

## Installation Steps

### Step 1: Verify Python Installation

Open terminal or command prompt and verify Python version:

```bash
python --version
# or
python3 --version
```

Expected output: `Python 3.8.x` or higher

If Python is not installed:
- **Windows**: Download from [python.org](https://www.python.org/downloads/)
- **macOS**: Install via Homebrew: `brew install python3`
- **Linux**: `sudo apt-get install python3 python3-pip`

---

### Step 2: Download Application

Download the complete package or clone repository:

```bash
# Option 1: Download ZIP
# Extract to desired location

# Option 2: Clone repository (if available)
git clone [repository-url]
cd word-to-elementor
```

---

### Step 3: Install Dependencies

Navigate to application directory:

```bash
cd word-to-elementor
```

Install required Python packages:

```bash
pip install -r requirements.txt
```

Or with pip3:

```bash
pip3 install -r requirements.txt
```

Expected output:
```
Successfully installed streamlit-x.x.x python-docx-x.x.x Pillow-x.x.x
```

---

### Step 4: Verify Installation

Check if all dependencies are installed:

```bash
pip list | grep streamlit
pip list | grep python-docx
pip list | grep Pillow
```

All three packages should appear in the list.

---

### Step 5: Launch Application

Start the application:

```bash
streamlit run app_optimized.py
```

Expected output:
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

The application will automatically open in your default browser.

---

## Configuration

### Port Configuration

If port 8501 is already in use, specify a different port:

```bash
streamlit run app_optimized.py --server.port 8502
```

### Browser Configuration

Disable automatic browser opening:

```bash
streamlit run app_optimized.py --server.headless true
```

### Theme Configuration

The application uses a professional light theme by default. To customize, create `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#1e40af"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f9fafb"
textColor = "#374151"
font = "sans serif"
```

---

## Troubleshooting

### Issue: "streamlit: command not found"

**Solution:**
```bash
# Add Python scripts to PATH
export PATH="$HOME/.local/bin:$PATH"

# Or use python -m
python -m streamlit run app_optimized.py
```

---

### Issue: "No module named 'docx'"

**Solution:**
```bash
pip install python-docx
# Not just 'docx'
```

---

### Issue: "Permission denied"

**Solution:**
```bash
# Install packages for current user only
pip install --user -r requirements.txt

# Or use sudo (Linux/macOS)
sudo pip install -r requirements.txt
```

---

### Issue: Port Already in Use

**Solution:**
```bash
# Find process using port 8501
# Windows:
netstat -ano | findstr :8501

# macOS/Linux:
lsof -i :8501

# Kill process or use different port
streamlit run app_optimized.py --server.port 8502
```

---

## WordPress Configuration

### Elementor Installation

1. Log in to WordPress Admin Dashboard
2. Navigate to Plugins > Add New
3. Search for "Elementor"
4. Click "Install Now" then "Activate"

### Template Import Setup

Enable template import in Elementor:

1. Navigate to Elementor > Settings
2. Go to Features tab
3. Enable "Import/Export Kit"
4. Save changes

### Media Library Preparation

Create organized folder structure:

1. Navigate to Media > Library
2. Create folder: `/wp-content/uploads/2024/11/`
3. Note the complete URL for later use

---

## Verification

### Application Verification

After installation, verify all features work:

1. Launch application
2. Check sidebar displays correctly
3. Verify logo appears
4. Test file upload
5. Perform test conversion
6. Download results

### WordPress Verification

Verify WordPress is ready:

1. Elementor plugin active
2. Import/Export enabled
3. Media library accessible
4. Template library accessible

---

## Post-Installation

### First Use Checklist

- [ ] Application launches successfully
- [ ] All dependencies installed
- [ ] Logo and UI elements display correctly
- [ ] Test document converts successfully
- [ ] WordPress configuration complete
- [ ] Media library URL noted
- [ ] User guide reviewed

### Recommended Next Steps

1. Read [USER_GUIDE.md](USER_GUIDE.md) for usage instructions
2. Review [README.md](README.md) for feature overview
3. Explore [GUIDE_LAYOUTS.md](GUIDE_LAYOUTS.md) for layout options
4. Test with sample documents
5. Configure WordPress Media URL

---

## Updating

### Update Application

When new version is released:

```bash
# Download new version
# Replace files in application directory
# Update dependencies
pip install --upgrade -r requirements.txt

# Restart application
streamlit run app_optimized.py
```

### Check Version

Current version displayed in:
- Application sidebar
- About page
- README.md file

---

## Uninstallation

### Remove Application

Simply delete the application directory:

```bash
# Delete folder
rm -rf word-to-elementor

# Or move to trash on Windows/macOS
```

### Remove Dependencies (Optional)

To remove installed Python packages:

```bash
pip uninstall streamlit python-docx Pillow
```

---

## Support

### Installation Issues

If you encounter installation problems:

**Contact Information:**
- Email: contact@bendatainsights.cloud
- Website: bendatainsights.cloud

**Include in support request:**
- Operating system and version
- Python version
- Error messages (screenshots)
- Installation steps completed

### Documentation

For additional help:
- [USER_GUIDE.md](USER_GUIDE.md) - Usage instructions
- [README.md](README.md) - Feature overview
- [CHANGELOG.md](CHANGELOG.md) - Version history

---

## Security Notes

### Safe Usage

- Only install from official sources
- Verify requirements.txt before installation
- Keep Python and packages updated
- Use secure WordPress passwords
- Backup WordPress before importing templates

### Data Privacy

- Documents processed locally
- No data sent to external servers
- Images stored temporarily in outputs/
- Clear cache regularly for privacy

---

## Advanced Configuration

### Production Deployment

For production environments:

```bash
# Use specific host
streamlit run app_optimized.py --server.address 0.0.0.0

# Enable CORS if needed
streamlit run app_optimized.py --server.enableCORS false

# Set file upload limit (MB)
streamlit run app_optimized.py --server.maxUploadSize 100
```

### Docker Deployment

Create Dockerfile:

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app_optimized.py"]
```

Build and run:

```bash
docker build -t word-to-elementor .
docker run -p 8501:8501 word-to-elementor
```

---

**Installation Guide** - Word to Elementor Converter v3.0  
© 2024-2025 Zakaria Benhoumad & HBN Consulting LTD
