# AgriPlot Vision - Drone Multispectral & Phenotyping Visualizer

An interactive agricultural web application built with **FastAPI**, **Plotly.js**, and **Tailwind CSS** to visualize and analyze plot-level reflectance, vegetative indices (NDVI, NDRE, CCC, TGI, VARI), and high-resolution drone imagery from `Tainan2024.csv`.

---

## 🌾 Dataset Overview (`Tainan2024.csv`)

- **Experiment**: TNDAIS 2024 2nd Season Sheath Blight Screening Trial
- **Institution**: National Taiwan University (NTU) & Tainan DARES
- **Total Plots**: 348 observation units
- **Germplasms**: 174 unique lines across 2 replicates
- **Field Layout**: 90 Rows × 4 Columns
  - **Columns 1–2**: Replicate 2 (174 plots)
  - **Columns 3–4**: Replicate 1 (174 plots)
- **Spectral Measurements (225 traits)**:
  - **Vegetation Indices**: NDVI (Normalized Difference Vegetation Index), NDRE (Red Edge NDVI), CCC (Canopy Chlorophyll Content), TGI (Triangular Greenness Index), VARI (Visible Atmospherically Resistant Index)
  - **Spectral Bands**: Blue (450–520nm), Green (515–600nm), Red (600–690nm), Red Edge (690–750nm), NIR (780–3000nm)
  - **Processing Variants**: Denoised Original Images and Thresholded (Background-Removed) Images
  - **Aggregations**: Mean, Median, Harmonic Mean, Std Dev, Variance, Min, Max, Pixel Counts
- **Multispectral Image Channels (18 per plot)**:
  - RGB Natural Color Imagery
  - Vegetation Index Imagery: NDVI, NDRE, CCC, TGI, VARI, NRN, NReN
  - Raw Band Imagery: Blue, Green, Red, Red Edge, NIR
  - Thresholded Background-Removed Imagery: Blue, Green, Red, Red Edge, NIR

---

## 🚀 Quick Start (Using Virtual Environment)

### 1. Ensure Dependencies are Installed in `.venv`
```bash
# If not already created:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Start the Web Server
You can launch the server using the provided `run.sh` script or directly with `uvicorn`:

```bash
./run.sh
```

Or directly via the virtual environment:
```bash
.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Open in Browser
- **Dashboard**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **FastAPI Interactive API Docs (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 📊 Key Features

### 1. 🗺️ Field Spatial Heatmap
- Visualizes the entire 90-row × 4-column greenhouse grid.
- Select any of the 225 spectral metrics or vegetation indices (e.g. Mean NDVI, NDRE, CCC, Red, NIR).
- Choose from multiple scientific color scales (Viridis, YlGn, Plasma, RdYlGn, etc.).
- **Interactive Plot Selection**: Clicking on any cell in the heatmap immediately displays that plot's metrics and loads its full 18-channel imagery in the Plot Inspector!

### 2. 📊 Distribution & Histogram Explorer
- View frequency distributions for any metric with configurable bin count (10 to 60).
- Toggle Gaussian Kernel Density Estimation (KDE) curve.
- Compare Replicate 1 vs Replicate 2 distributions overlaid or side-by-side.
- Statistical summary card reporting Mean, Median, Standard Deviation, Interquartile Range (IQR), and Skewness.

### 3. 📈 Relative Plots & Scatter Analysis
- Select any X-axis metric and Y-axis metric (e.g. NDVI vs NDRE, Red vs NIR reflectance, CCC vs TGI).
- Calculates ordinary least-squares linear regression ($y = mx + b$), coefficient of determination ($R^2$), Pearson correlation coefficient ($r$), and p-value.
- 1-click preset buttons for common agronomic comparisons.
- Color points by Replicate or Entry Type.

### 4. 🔥 Trait Correlation Matrix
- Computes pairwise Pearson correlation coefficients across all primary vegetation indices and multispectral bands.
- Helps identify colinear traits, spectral band sensitivities, and index robustness.

### 5. 🧬 Germplasm Performance Ranking
- Boxplots showing phenotypic distributions of the top (or lowest) germplasms across replicates.
- Useful for identifying disease-resistant lines with higher vegetative vigor (NDVI/CCC).

### 6. 🖼️ Plot Inspector & 18-Channel Image Viewer
- Select any plot or search by Plot Number / Germplasm name.
- **Spectral Signature Profile**: Plots the plot's reflectance curve across Blue (485nm), Green (560nm), Red (645nm), Red Edge (720nm), and NIR (840nm) against the field-wide average curve.
- **18-Channel Image Gallery**: Displays all RGB, index, raw band, and thresholded imagery.
- **Dual Image Comparison**: Side-by-side comparison mode allowing you to compare any two channels (e.g. RGB vs NDVI).
- **Fullscreen Zoom Modal**: Inspect high-res imagery with direct URL copying.
- Built-in graceful fallbacks if remote origins are offline or require local network access.

---

## 🛠️ Web Endpoints (`/plot` Prefix)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` or `/plot` | Serves the interactive web dashboard |
| `GET` | `/plot/info` | General study metadata and column catalog |
| `GET` | `/plot/traits` | List of all 225 metrics with aliases and categories |
| `GET` | `/plot/images` | Catalog of 18 multispectral image channels |
| `GET` | `/plot/plots` | Search and filter plots |
| `GET` | `/plot/plots/{plot_id}` | Plot metadata, traits, spectral curve, and image URLs |
| `GET` | `/plot/field-heatmap` | 2D spatial grid values for field heatmap |
| `GET` | `/plot/distribution` | Histogram, KDE density, and summary statistics |
| `GET` | `/plot/scatter` | Scatter plot points and linear regression metrics |
| `GET` | `/plot/correlation-matrix` | Multi-trait Pearson correlation matrix |
| `GET` | `/plot/germplasm-ranking` | Boxplot data for top/bottom germplasms |
| `POST` | `/plot/upload` | Upload a new trial CSV dataset |
