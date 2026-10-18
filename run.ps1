# Smart Study Generator — Run Script
# Double-click this file or run:  powershell -ExecutionPolicy Bypass -File run.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Smart Study Generator" -ForegroundColor White
Write-Host "  Powered by IBM Granite + watsonx.ai" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Installing / verifying dependencies..." -ForegroundColor Green
python -m pip install streamlit plotly pandas Pillow python-docx PyMuPDF --quiet

Write-Host ""
Write-Host "Starting app at http://localhost:8501 ..." -ForegroundColor Green
Write-Host ""
python -m streamlit run app.py --server.port 8501
