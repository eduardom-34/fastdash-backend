from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from app.services.data_service import DataService
from app.services.ai_service import AIService
from app.models import UploadResponse, ChartParameters
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="AI Dashboard Builder API")

# Configuración CORS (Permitir frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://fastdash-frontend.vercel.app/"], # Ajusta el puerto de tu React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

data_service = DataService()
ai_service = AIService()

@app.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    # 1. Validar extensión
    if not file.filename.endswith(('.csv', '.xlsx')):
        raise HTTPException(status_code=400, detail="Formato no soportado. Use CSV o Excel.")

    try:
        # 2. Guardar archivo y cargar DataFrame
        file_id, file_path = data_service.save_file(file.file, file.filename)
        df = data_service.load_df(file_id, file.filename)
        
        # 3. Generar resumen estadístico
        summary = data_service.get_summary(df)
        
        # 4. Consultar a la IA
        suggestions = ai_service.analyze_data(summary)
        
        return UploadResponse(
            file_id=file_id,
            filename=file.filename,
            summary="Análisis completado exitosamente.",
            suggestions=suggestions
        )

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chart-data")
async def get_chart_data(
    file_id: str, 
    filename: str, 
    x_axis: str, 
    y_axis: str, 
    chart_type: str = "bar"
):
    try:
        # 1. Recargar el DataFrame
        df = data_service.load_df(file_id, filename)
        
        # 2. Procesar y agregar datos
        params = {"x_axis": x_axis, "y_axis": y_axis, "chart_type": chart_type}
        chart_data = data_service.process_chart_data(df, params)
        
        return chart_data
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Archivo no encontrado o sesión expirada")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)