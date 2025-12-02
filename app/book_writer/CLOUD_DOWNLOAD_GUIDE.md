# Cloud Download Guide

## Downloading Generated Books from Cloud Environments

When running the book writer CLI in a cloud environment (Runpod, AWS, GCP, etc.), you need to transfer files to your local computer. This guide shows you how.

## Quick Start

The CLI automatically creates a **ZIP archive** containing all generated files. This is the easiest way to download everything at once.

### File Structure

After generation, you'll find in the output directory:

```
book_outputs/
├── {Book_Title}_package.json      # Complete book data
├── {Book_Title}_chat_log.json     # Agent communications
├── {Book_Title}_book.pdf          # PDF file (if generated)
└── {Book_Title}_complete.zip      # 📦 ALL FILES IN ONE ARCHIVE
```

## Download Methods

### Method 1: Download ZIP Archive (Recommended)

The easiest way is to download the complete ZIP archive:

```bash
# Using SCP
scp user@cloud-host:/path/to/book_outputs/{Book_Title}_complete.zip ./

# Using SFTP
sftp user@cloud-host
cd /path/to/book_outputs
get {Book_Title}_complete.zip
quit

# Using rsync
rsync -avz user@cloud-host:/path/to/book_outputs/{Book_Title}_complete.zip ./
```

### Method 2: Download Individual Files

If you only need specific files:

```bash
# Download JSON package
scp user@cloud-host:/path/to/book_outputs/{Book_Title}_package.json ./

# Download PDF
scp user@cloud-host:/path/to/book_outputs/{Book_Title}_book.pdf ./

# Download chat log
scp user@cloud-host:/path/to/book_outputs/{Book_Title}_chat_log.json ./
```

### Method 3: Download Entire Directory

Download all files at once:

```bash
# Using rsync (recommended)
rsync -avz user@cloud-host:/path/to/book_outputs/ ./book_downloads/

# Using SCP
scp -r user@cloud-host:/path/to/book_outputs/ ./book_downloads/
```

## Cloud-Specific Instructions

### Runpod

1. **Using Runpod Web Interface:**
   - Go to your pod's file browser
   - Navigate to the output directory
   - Download files directly from the web interface

2. **Using SSH:**
   ```bash
   # Connect to your Runpod
   ssh root@your-runpod-ip
   
   # Find your files
   cd /path/to/book_outputs
   ls -lh
   
   # Download via SCP from your local machine
   scp root@your-runpod-ip:/path/to/book_outputs/{Book_Title}_complete.zip ./
   ```

### AWS EC2

```bash
# From your local machine
scp -i your-key.pem ec2-user@your-ec2-ip:/path/to/book_outputs/{Book_Title}_complete.zip ./
```

### Google Cloud Platform

```bash
# Using gcloud compute scp
gcloud compute scp instance-name:/path/to/book_outputs/{Book_Title}_complete.zip ./

# Or using regular SCP
scp user@your-gcp-ip:/path/to/book_outputs/{Book_Title}_complete.zip ./
```

### Azure

```bash
# Using Azure CLI
az vm run-command invoke --resource-group myResourceGroup --name myVM \
  --command-id RunShellScript --scripts "cat /path/to/book_outputs/{Book_Title}_complete.zip" > output.zip

# Or using SCP
scp user@your-azure-ip:/path/to/book_outputs/{Book_Title}_complete.zip ./
```

## Using Cloud Storage Services

### Upload to S3 (AWS)

```bash
# From cloud instance
aws s3 cp book_outputs/{Book_Title}_complete.zip s3://your-bucket/books/

# Download from local machine
aws s3 cp s3://your-bucket/books/{Book_Title}_complete.zip ./
```

### Upload to Google Cloud Storage

```bash
# From cloud instance
gsutil cp book_outputs/{Book_Title}_complete.zip gs://your-bucket/books/

# Download from local machine
gsutil cp gs://your-bucket/books/{Book_Title}_complete.zip ./
```

### Upload to Azure Blob Storage

```bash
# From cloud instance
az storage blob upload --account-name yourstorage --container-name books \
  --name {Book_Title}_complete.zip --file book_outputs/{Book_Title}_complete.zip

# Download from local machine
az storage blob download --account-name yourstorage --container-name books \
  --name {Book_Title}_complete.zip --file ./{Book_Title}_complete.zip
```

## Using File Transfer Services

### Using FileZilla (GUI)

1. Connect to your cloud server via SFTP
2. Navigate to the output directory
3. Download the ZIP file or individual files

### Using WinSCP (Windows)

1. Connect to your cloud server
2. Navigate to the output directory
3. Drag and drop files to your local computer

## Verifying Downloads

After downloading, verify the files:

```bash
# Check ZIP file
unzip -l {Book_Title}_complete.zip

# Extract ZIP
unzip {Book_Title}_complete.zip

# Verify JSON
cat {Book_Title}_package.json | python3 -m json.tool > /dev/null && echo "JSON is valid"

# Check PDF
file {Book_Title}_book.pdf  # Should show "PDF document"
```

## Troubleshooting

### Issue: "Permission denied" when downloading

**Solution:**
```bash
# Make sure files are readable
chmod 644 book_outputs/*

# Or download as the file owner
sudo scp user@cloud-host:/path/to/book_outputs/{Book_Title}_complete.zip ./
```

### Issue: Files not found

**Solution:**
```bash
# Check the exact path shown in CLI output
# The CLI shows the full absolute path
# Use that exact path in your download command
```

### Issue: Large file downloads timeout

**Solution:**
```bash
# Use rsync with resume capability
rsync -avz --partial --progress user@cloud-host:/path/to/book_outputs/ ./

# Or split large files
split -b 100M {Book_Title}_complete.zip {Book_Title}_complete.zip.part
# Then download parts and combine:
cat {Book_Title}_complete.zip.part* > {Book_Title}_complete.zip
```

## Best Practices

1. **Always download the ZIP archive** - It contains everything in one file
2. **Verify file integrity** - Check file sizes match
3. **Keep backups** - Don't delete files from cloud until verified locally
4. **Use cloud storage** - Upload to S3/GCS for permanent storage
5. **Organize by date** - Use dated output directories for multiple books

## Example Workflow

```bash
# 1. Run book generation in cloud
python3 -m app.book_writer.ferrari_company

# 2. Note the output directory path from CLI output
# Example: /home/user/book_outputs/

# 3. Download ZIP archive
scp user@cloud-host:/home/user/book_outputs/Exile_to_Mars_complete.zip ./

# 4. Extract locally
unzip Exile_to_Mars_complete.zip

# 5. Verify files
ls -lh
# Should see: package.json, chat_log.json, book.pdf
```

## Need Help?

If you encounter issues:
1. Check the CLI output for exact file paths
2. Verify SSH/SCP access to your cloud instance
3. Check file permissions on the cloud server
4. Try downloading individual files if ZIP fails

