import json
from openai import OpenAI
from app.models import AIAnalysisSuggestion

class AIService:
    def __init__(self):
        # Asegúrate de tener OPENAI_API_KEY en tus variables de entorno
        self.client = OpenAI()

    def analyze_data(self, data_summary: str) -> list[AIAnalysisSuggestion]:
        system_prompt = """
        Eres un Analista de Datos Senior experto. Tu objetivo es analizar la estructura de un dataset
        y sugerir 3 visualizaciones perspicaces que ayuden a un usuario de negocio a entender sus datos.
        
        REGLAS:
        1. Devuelve SOLO un objeto JSON con una clave "suggestions" que sea una lista.
        2. Cada sugerencia DEBE tener un campo 'title' (título corto y descriptivo).
        3. Cada sugerencia DEBE tener un campo 'chart_type'. Los valores permitidos son: "bar", "line", "pie", "scatter".
        4. El campo 'insight' debe ser una frase breve y clara en español explicando qué muestra el gráfico.
        5. El campo 'parameters' debe contener 'x_axis' y 'y_axis' basados EXACTAMENTE en los nombres de columnas provistos.
        6. Elige columnas numéricas para el eje Y y categóricas/temporales para el eje X (excepto en scatter).
        """

        user_prompt = f"""
        Aquí está el resumen del dataset (columnas, tipos y muestra de datos):
        
        {data_summary}
        
        Genera las sugerencias de análisis ahora.
        """

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo-0125", # O gpt-4o-mini que es más barato y rápido
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )

        try:
            content = response.choices[0].message.content
            data = json.loads(content)
            # Validamos y convertimos a nuestros modelos Pydantic
            return data.get("suggestions", [])
        except Exception as e:
            print(f"Error parsing AI response: {e}")
            return []