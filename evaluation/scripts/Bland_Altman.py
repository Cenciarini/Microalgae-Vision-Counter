import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from scipy.stats import shapiro, probplot, pearsonr

# CONFIGURACIÓN DE ESTILO PARA GRÁFICAS (Estilo Tesis)
plt.style.use('seaborn-v0_8-whitegrid')
params = {'axes.labelsize': 12, 'axes.titlesize': 14, 'legend.fontsize': 11, 'font.family': 'serif'}
plt.rcParams.update(params)

def main():
    # 1. CARGA DE DATOS
    try:
        df = pd.read_excel("Analisis_Datos_Val.xlsx")
        x = df['Manual'].values
        y = df['Automatico'].values
        print("Datos cargados correctamente.")
    except Exception as e:
        print(f"Error al cargar el archivo: {e}")
        return


    # ANÁLISIS DE RESIDUOS Y NORMALIDAD
    diff_raw = y - x
    
    # Transformación Logarítmica
    lx = np.log(x)
    ly = np.log(y)
    diff_log = ly - lx
    mean_log = (lx + ly) / 2
    
    # Test de Shapiro-Wilk
    shapiro_raw = shapiro(diff_raw)
    shapiro_log = shapiro(diff_log)

    print("\n--- NORMALIDAD DE RESIDUOS (SHAPIRO-WILK) ---")
    print(f"Originales (p-valor): {shapiro_raw.pvalue:.4f} {'(No Normal)' if shapiro_raw.pvalue < 0.05 else '(Normal)'}")
    print(f"Log-transformados (p-valor): {shapiro_log.pvalue:.4f} {'(No Normal)' if shapiro_log.pvalue < 0.05 else '(Normal)'}")

    # --- FIGURA 1: NORMALIDAD ---
    fig1, axs = plt.subplots(2, 2, figsize=(12, 10))
    fig1.suptitle("Análisis de Normalidad: Residuos Originales vs Logarítmicos", fontsize=16)

    # Fila 1: Datos Originales
    axs[0, 0].hist(diff_raw, bins=15, color='skyblue', edgecolor='black', alpha=0.7)
    axs[0, 0].set_title(f"Histograma Residuos Originales\n(Shapiro p={shapiro_raw.pvalue:.3f})")
    axs[0, 0].set_xlabel("Diferencia (Auto - Manual)")
    
    probplot(diff_raw, dist="norm", plot=axs[0, 1])
    axs[0, 1].set_title("Q-Q Plot Residuos Originales")

    # Fila 2: Datos Logarítmicos
    axs[1, 0].hist(diff_log, bins=15, color='lightgreen', edgecolor='black', alpha=0.7)
    axs[1, 0].set_title(f"Histograma Residuos Log\n(Shapiro p={shapiro_log.pvalue:.3f})")
    axs[1, 0].set_xlabel("Diferencia Log (ln(Auto) - ln(Manual))")

    probplot(diff_log, dist="norm", plot=axs[1, 1])
    axs[1, 1].set_title("Q-Q Plot Residuos Logarítmicos")

    plt.tight_layout()
    plt.savefig('analisis_normalidad.png', dpi=300)
    print("Gráfica guardada: analisis_normalidad.png")

    # 4. BLAND-ALTMAN ROBUSTO (REGRESIÓN)
    # Modelar Sesgo (Tendencia central)
    X_design = sm.add_constant(mean_log)
    model_bias = sm.OLS(diff_log, X_design).fit()
    b0, b1 = model_bias.params # b0: intercepto, b1: pendiente del sesgo
    
    # Modelar Heterocedasticidad (Límites variables)
    # Regresión de residuos absolutos vs media
    abs_resid = np.abs(model_bias.resid)
    model_het = sm.OLS(abs_resid, X_design).fit()
    g0, g1 = model_het.params
    
    # Calcular líneas para el gráfico (ordenadas)
    sort_idx = np.argsort(mean_log)
    m_sorted = mean_log[sort_idx]
    
    # Ecuaciones
    bias_line = b0 + b1 * m_sorted
    sd_modeled = (g0 + g1 * m_sorted) * np.sqrt(np.pi / 2) # SD estimada
    upper_loa = bias_line + 1.96 * sd_modeled
    lower_loa = bias_line - 1.96 * sd_modeled

    # --- FIGURA 2: BLAND-ALTMAN ROBUSTO ---
    plt.figure(figsize=(10, 7))
    
    # Scatter plot
    plt.scatter(mean_log, diff_log, alpha=0.6, color='navy', label='Datos Observados')
    
    # Líneas de regresión
    plt.plot(m_sorted, bias_line, 'r-', linewidth=2, label='Sesgo Regresado (Media)')
    plt.plot(m_sorted, upper_loa, 'r--', linewidth=2, label='Límites de Acuerdo (95%)')
    plt.plot(m_sorted, lower_loa, 'r--', linewidth=2)
    
    # Línea cero (referencia ideal)
    plt.axhline(0, color='gray', linestyle=':', alpha=0.8)

    # Etiquetas y Títulos
    plt.title("Bland-Altman Robusto (Escala Logarítmica)\nAjuste por Heterocedasticidad", fontsize=16)
    plt.xlabel("Promedio de Logaritmos: (ln(Manual) + ln(Auto))/2", fontsize=12)
    plt.ylabel("Diferencia de Logaritmos: ln(Auto) - ln(Manual)", fontsize=12)
    
    # Ecuación en el gráfico
    eq_text = (f"Sesgo = {b0:.3f} + {b1:.3f}x\n"
               f"SD(x) = ({g0:.3f} + {g1:.3f}x) * √(π/2)")
    plt.text(0.05, 0.95, eq_text, transform=plt.gca().transAxes, 
             fontsize=10, verticalalignment='top', 
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.legend(loc='lower right')
    plt.tight_layout()
    plt.savefig('bland_altman_robusto.png', dpi=300)
    print("Gráfica guardada: bland_altman_robusto.png")

if __name__ == "__main__":
    main()