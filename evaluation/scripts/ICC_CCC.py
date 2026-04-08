import pandas as pd
import numpy as np
from scipy import stats
import pingouin as pg
import matplotlib.pyplot as plt
import seaborn as sns

def calcular_icc_ccc(manual, auto):
    """Función auxiliar para calcular ICC y CCC de dos series de datos."""
    temp_df = pd.DataFrame({'Manual': manual, 'Automatico': auto}).reset_index()
    df_long = pd.melt(temp_df, id_vars=['index'], value_vars=['Manual', 'Automatico'])
    
    icc = pg.intraclass_corr(data=df_long, targets='index', raters='variable', ratings='value')
    icc_val = icc.set_index('Type').loc['ICC2', 'ICC']
    icc_ci = icc.set_index('Type').loc['ICC2', 'CI95%']

    cor = np.corrcoef(manual, auto)[0, 1]
    mean_m, mean_a = np.mean(manual), np.mean(auto)
    var_m, var_a = np.var(manual, ddof=1), np.var(auto, ddof=1)
    sd_m, sd_a = np.sqrt(var_m), np.sqrt(var_a)
    
    ccc = (2 * cor * sd_m * sd_a) / (var_m + var_a + (mean_m - mean_a)**2)
    
    return icc_val, icc_ci, ccc

def graficar_concordancia(manual, auto, icc_val, ccc_val, tipo_datos):
    """
    Genera el gráfico de dispersión con Línea de Identidad.
    Es la representación visual directa del CCC y el ICC.
    """
    plt.figure(figsize=(8, 8))
    
    # Puntos reales
    sns.scatterplot(x=manual, y=auto, alpha=0.7, color='#2ca02c', edgecolor='black', s=60)
    
    # Línea de regresión (Tendencia de la predicción)
    sns.regplot(x=manual, y=auto, scatter=False, color='red', 
                line_kws={'linestyle':'--', 'label':'Tendencia de los datos (Regresión)'})
    
    # Línea de Identidad (Concordancia perfecta Y = X)
    limite_min = min(min(manual), min(auto))
    limite_max = max(max(manual), max(auto))
    margen = (limite_max - limite_min) * 0.05
    
    plt.plot([limite_min - margen, limite_max + margen], 
             [limite_min - margen, limite_max + margen], 
             color='black', linestyle='-', linewidth=2.5, 
             label='Concordancia Perfecta ($Y=X$)')

    # Ajustes estéticos
    plt.title(f'Concordancia de Conteo: Manual vs. Sistema Automático\n(Datos {tipo_datos})', 
              fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Conteo Manual (Microalgas)', fontsize=12)
    plt.ylabel('Conteo Automático (YOLOv5)', fontsize=12)
    
    # Caja de texto con los resultados
    texto_resultados = f"ICC (2,1): {icc_val:.4f}\nCCC (Lin): {ccc_val:.4f}"
    plt.text(0.05, 0.95, texto_resultados, transform=plt.gca().transAxes, 
             fontsize=12, verticalalignment='top', 
             bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='gray', alpha=0.9))
    
    plt.legend(loc='lower right')
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.tight_layout()
    
    # Guardar imagen
    nombre_archivo = f'Concordancia_Dispersion_{tipo_datos}.png'
    plt.savefig(nombre_archivo, dpi=300)
    plt.close()
    print(f"\n[+] Gráfico exportado con éxito para la presentación: {nombre_archivo}")

def analizar_concordancia(file_path):
    try:
        df = pd.read_excel(file_path)
        if 'Manual' not in df.columns or 'Automatico' not in df.columns:
            return print("Error: Las columnas 'Manual' y 'Automatico' no se encuentran.")

        manual = df['Manual']
        auto = df['Automatico']
        diferencias = manual - auto

        print("--- ANÁLISIS DE NORMALIDAD (DATOS ORIGINALES) ---")
        shapiro_diff = stats.shapiro(diferencias)
        es_normal = shapiro_diff.pvalue > 0.05
        print(f"Diferencias: p={shapiro_diff.pvalue:.4f} -> {'NORMAL' if es_normal else 'NO NORMAL'}")

        if not es_normal:
            print("\n[!] ALERTA: Diferencias no normales. Aplicando transformación LOGARÍTMICA...")
            manual_final = np.log(manual + 1e-6)
            auto_final = np.log(auto + 1e-6)
            tipo_datos = "Logarítmicos"
        else:
            manual_final = manual
            auto_final = auto
            tipo_datos = "Originales"

        icc_val, icc_ci, ccc = calcular_icc_ccc(manual_final, auto_final)

        # Generar gráfico
        graficar_concordancia(manual_final, auto_final, icc_val, ccc_val=ccc, tipo_datos=tipo_datos)

        def interpret_icc(val):
            if val < 0.5: return "Pobre"
            if val < 0.75: return "Moderada"
            if val < 0.9: return "Buena"
            return "Excelente"

        def interpret_ccc(val):
            if val < 0.90: return "Pobre/Insuficiente"
            if val < 0.95: return "Moderada"
            if val < 0.99: return "Sustancial"
            return "Casi Perfecta"

        print(f"\n--- RESULTADOS (Escala: {tipo_datos}) ---")
        print(f"ICC (2,1): {icc_val:.4f} ({interpret_icc(icc_val)})")
        print(f"IC 95% ICC: {icc_ci}")
        print(f"CCC de Lin: {ccc:.4f} ({interpret_ccc(ccc)})")

        print("\n--- CONCLUSIÓN FINAL ---")
        if icc_val > 0.75 and ccc > 0.90:
            print(f"Resultado: CONFIABLE. Concordancia sólida en escala {tipo_datos.lower()}.")
        else:
            print("Resultado: BAJA CONCORDANCIA. Revisar sesgo entre métodos.")

    except Exception as e:
        print(f"Error durante la ejecución: {e}")

if __name__ == "__main__":
    analizar_concordancia("Analisis_Datos_Val.xlsx")