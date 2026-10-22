"""
FastAPI Backend Application for Agricultural Drone Multispectral & Vegetation Index Visualization.
Serves REST API endpoints for spatial field heatmaps, histograms, scatter/relative plots,
correlation matrices, and plot image visualization.
"""

import os
import shutil
from typing import Optional, List
from fastapi import FastAPI, APIRouter, HTTPException, Query, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment, FileSystemLoader

from data_manager import DataManager

app = FastAPI(
    title="AgriPlot Vision - Multispectral & Phenotyping Visualizer",
    description="Interactive web backend and visualization platform for reflectance, vegetation indices, and plot imagery.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DataManager with default CSV
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(BASE_DIR, "Tainan2024.csv")
data_manager = DataManager(DEFAULT_CSV)

# Templates setup
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

jinja_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Router with '/plot' prefix
plot_router = APIRouter(prefix="/plot", tags=["Plot Phenotyping & Visualizations"])


@app.get("/", response_class=HTMLResponse)
@plot_router.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serves the main interactive visualization dashboard."""
    template = jinja_env.get_template("index.html")
    metadata = data_manager.get_metadata_summary()
    return HTMLResponse(content=template.render(metadata=metadata))


# ==================== DATA & VISUALIZATION ENDPOINTS (/plot/... PREFIX) ====================

@plot_router.get("/info")
async def get_study_info():
    """Returns general study metadata and experiment metrics."""
    return data_manager.get_metadata_summary()


@plot_router.get("/traits")
async def get_traits(
    category: Optional[str] = Query(None, description="Filter by category (Vegetation Indices, Reflectance Bands, Thresholded Bands)"),
    stat: Optional[str] = Query(None, description="Filter by statistic (Mean Pixel Value, Median Pixel Value, etc.)")
):
    """Returns the catalog of available traits and measurement variables."""
    return data_manager.get_traits(category=category, stat=stat)


@plot_router.get("/images")
async def get_images_catalog():
    """Returns the list of 18 available image channels and categories."""
    return data_manager.get_image_list()


@plot_router.get("/plots")
@plot_router.get("/list")
async def search_plots(
    query: Optional[str] = Query("", description="Search by plotNumber or germplasmName"),
    replicate: Optional[int] = Query(None, description="Filter by replicate (1 or 2)")
):
    """Returns matching plots with metadata."""
    return data_manager.search_plots(query=query, replicate=replicate)


@plot_router.get("/field-heatmap")
@plot_router.get("/field_heatmap")
async def get_field_heatmap(
    metric: Optional[str] = Query(None, description="Metric column or alias (default: Mean NDVI)"),
    replicate: Optional[int] = Query(None, description="Filter by replicate (1 or 2)")
):
    """Returns 2D spatial grid data for field heatmap (Row 1-90 x Col 1-4)."""
    metric_col = metric or data_manager.get_default_metric()
    return data_manager.get_field_heatmap_data(metric_col=metric_col, replicate=replicate)


@plot_router.get("/distribution")
async def get_distribution(
    metric: Optional[str] = Query(None, description="Metric column or alias"),
    replicate: Optional[int] = Query(None, description="Filter by replicate (1 or 2)"),
    bins: Optional[int] = Query(25, ge=5, le=100, description="Number of histogram bins")
):
    """Returns histogram, density/KDE data, and summary statistics."""
    metric_col = metric or data_manager.get_default_metric()
    return data_manager.get_distribution_data(metric_col=metric_col, replicate=replicate, num_bins=bins)


@plot_router.get("/scatter")
async def get_scatter(
    x: Optional[str] = Query(None, description="X-axis metric"),
    y: Optional[str] = Query(None, description="Y-axis metric"),
    color_by: Optional[str] = Query("replicate", description="Variable to color points by"),
    replicate: Optional[int] = Query(None, description="Filter by replicate (1 or 2)")
):
    """Returns scatter plot points, linear regression line, and correlation metrics."""
    x_metric = x or data_manager.get_default_metric()
    # Default Y metric to NDRE if X is NDVI
    y_metric = y
    if not y_metric:
        ndre_match = next((t["column"] for t in data_manager.trait_catalog if t["statistic"] == "Mean Pixel Value" and "NDRE" in t["subtype"]), None)
        y_metric = ndre_match or x_metric

    return data_manager.get_scatter_data(
        x_metric=x_metric,
        y_metric=y_metric,
        color_by=color_by,
        replicate=replicate
    )


@plot_router.get("/correlation-matrix")
@plot_router.get("/correlation_matrix")
async def get_correlation_matrix(
    traits: Optional[str] = Query(None, description="Comma-separated list of traits or aliases")
):
    """Returns pairwise Pearson correlation matrix across selected traits."""
    trait_list = [t.strip() for t in traits.split(",")] if traits else None
    return data_manager.get_correlation_matrix(trait_aliases=trait_list)


@plot_router.get("/germplasm-ranking")
@plot_router.get("/germplasm_ranking")
async def get_germplasm_ranking(
    metric: Optional[str] = Query(None, description="Metric column or alias"),
    top_n: Optional[int] = Query(15, ge=3, le=50, description="Top N germplasms to rank"),
    ascending: Optional[bool] = Query(False, description="Ascending sort (lowest first)")
):
    """Returns top germplasms grouped across replicates for performance boxplots."""
    metric_col = metric or data_manager.get_default_metric()
    return data_manager.get_germplasm_ranking(metric_col=metric_col, top_n=top_n, ascending=ascending)


@plot_router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """Allows uploading a new or updated CSV file."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    upload_path = os.path.join(BASE_DIR, f"uploaded_{file.filename}")
    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    global data_manager
    try:
        new_dm = DataManager(upload_path)
        data_manager = new_dm
        return {
            "status": "success",
            "message": f"Successfully loaded '{file.filename}'",
            "info": data_manager.study_info
        }
    except Exception as e:
        if os.path.exists(upload_path):
            os.remove(upload_path)
        raise HTTPException(status_code=400, detail=f"Failed to load CSV: {str(e)}")


@plot_router.get("/plots/{plot_identifier}")
@plot_router.get("/detail/{plot_identifier}")
@plot_router.get("/{plot_identifier}")
async def get_plot_details(plot_identifier: str):
    """Returns comprehensive details for a specific plot, including traits, spectral curve, and images."""
    details = data_manager.get_plot_details(plot_identifier)
    if not details:
        raise HTTPException(status_code=404, detail=f"Plot '{plot_identifier}' not found.")
    return details


# Include router in FastAPI app
app.include_router(plot_router)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
