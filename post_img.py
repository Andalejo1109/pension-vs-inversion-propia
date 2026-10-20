import pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
plt.rcParams.update({"font.family":"DejaVu Sans","axes.spines.top":False,"axes.spines.right":False})
COL=pd.read_csv("colpensiones.csv"); AFP=pd.read_csv("afp.csv"); INV=pd.read_csv("inversion_propia.csv"); SML=1_750_905
f=lambda x:f"${x/1e6:.2f} M".replace(".",",")
fig=plt.figure(figsize=(7.2,9),dpi=150); fig.patch.set_facecolor("white")
fig.text(.5,.965,"Pensión obligatoria vs. invertir por tu cuenta",ha="center",fontsize=17,weight="bold",color="#1d3557")
fig.text(.5,.937,"Cotizando sobre 2 salarios mínimos · 20 o 25 años · COP de 2026",ha="center",fontsize=10.5,color="#444")
# Panel 1
a1=fig.add_axes([.12,.66,.83,.22]); cases=[("Mujer",20),("Mujer",25),("Hombre",20),("Hombre",25)]
import numpy as np; x=np.arange(4); w=.38
for i,(sx,an) in enumerate(cases):
  c=COL[(COL.sexo==sx)&(COL.anios==an)].iloc[0]; a=AFP[(AFP.sexo==sx)&(AFP.anios==an)&(AFP.rent_real==0.04)].iloc[0]
  vc=c.pension_SMLMV*SML; va=SML if "garant" in a.resultado_edad else 0
  a1.bar(i-w/2,vc/1e6,w,color="#1d3557"); a1.bar(i+w/2,va/1e6,w,color="#e9c46a")
  a1.text(i-w/2,(vc/1e6+.05) if vc else .75,f(vc) if vc else "Indemni-\nzación",ha="center",fontsize=7.5,va="bottom")
  a1.text(i+w/2,va/1e6+.05,"Mínima\n"+f(va) if va else "Devolución\nde saldos",ha="center",fontsize=7.5,va="bottom")
a1.set_xticks(x,[f"{s} {a} años\n(desde {57 if s=='Mujer' else 62})" for s,a in cases],fontsize=8.5); a1.set_ylim(0,3.1); a1.set_ylabel("Millones COP/mes",fontsize=9)
a1.bar(0,0,color="#1d3557",label="Colpensiones");a1.bar(0,0,color="#e9c46a",label="AFP (4% real)");a1.legend(fontsize=8,frameon=False,loc="upper left",ncol=2)
a1.set_title("1. Mesada a la edad mínima (57 mujeres / 62 hombres)",fontsize=11.5,weight="bold",loc="left",color="#1d3557")
# Panel 2
a2=fig.add_axes([.12,.36,.83,.21]); d=INV[INV.escenario=="bootstrap core"].sort_values(["anios","aporte_usd"])
lab=[f"{r.aporte_usd} USD/mes\n{r.anios} años" for _,r in d.iterrows()]; x=np.arange(len(d))
a2.bar(x-w/2,d.ingreso_4pct_mes_P50_COP/1e6,w,color="#2a9d8f",label="Escenario típico (P50)"); a2.bar(x+w/2,d.ingreso_4pct_mes_P10_COP/1e6,w,color="#a8dadc",label="Escenario malo (P10)")
for i,(_,r) in enumerate(d.iterrows()):
  a2.text(i-w/2,r.ingreso_4pct_mes_P50_COP/1e6+.05,f(r.ingreso_4pct_mes_P50_COP),ha="center",fontsize=7.5); a2.text(i+w/2,r.ingreso_4pct_mes_P10_COP/1e6+.05,f(r.ingreso_4pct_mes_P10_COP),ha="center",fontsize=7.5)
a2.set_xticks(x,lab,fontsize=8.5); a2.set_ylim(0,3.3); a2.set_ylabel("Millones COP/mes",fontsize=9); a2.legend(fontsize=8,frameon=False,loc="upper left")
a2.set_title("2. Cuenta propia (core eToro): ingreso al 4% desde los 50",fontsize=11.5,weight="bold",loc="left",color="#1d3557")
# Panel 3 timeline
a3=fig.add_axes([.06,.135,.88,.15]); a3.axis("off"); a3.set_xlim(23,66); a3.set_ylim(-1.3,1.6)
a3.text(23,1.45,"3. La secuencia",fontsize=11.5,weight="bold",color="#1d3557")
a3.plot([25,64],[0,0],color="#999",lw=2)
a3.add_patch(plt.Rectangle((25,-.18),25,.36,color="#a8dadc")); a3.text(37.5,.45,"Cotizas y además inviertes\n(25–30 → 50 años)",ha="center",fontsize=8.5)
a3.add_patch(plt.Rectangle((50,-.18),7,.36,color="#2a9d8f")); a3.add_patch(plt.Rectangle((57,-.18),5,.36,color="#52b788"))
a3.text(53.5,-.95,"Vives de tu inversión\n(el sistema aún no paga)",ha="center",fontsize=8,color="#1b4332")
for e,t in ((50,"50"),(57,"57 ♀"),(62,"62 ♂")):
  a3.plot([e,e],[-.3,.3],color="#1d3557",lw=2); a3.text(e,.3,t,ha="center",va="bottom",fontsize=9,weight="bold")
a3.text(62,-.95,"Pensión\n+ inversión",ha="center",fontsize=8,color="#1d3557")
fig.text(.5,.105,"Ni Colpensiones ni la AFP pagan antes de 57/62. Invertir por tu cuenta no reemplaza la cotización\n(es obligatoria): la complementa y te da libertad desde los 50.",ha="center",fontsize=8.7,weight="bold",color="#1d3557")
fig.text(.5,.045,"Régimen vigente (Ley 100). La reforma (Ley 2381/2024) entra en vigencia el 1-abr-2027 (C-264/26). AFP: 11,5% a la cuenta, 4% real.\nCore: SPYG/SMH/BRK.B/IEMG/VTI, 5.000 escenarios; USD a TRM 3.156,32; sin impuestos.\nEducativo, no es recomendación. Rentabilidades pasadas no garantizan futuras. Simulación 2003-2026, sesgo optimista.",ha="center",fontsize=6.8,color="#555",linespacing=1.4)
fig.text(.97,.012,"@Andalejo1109",ha="right",fontsize=9,weight="bold",color="#1d3557")
fig.savefig("post_pension_vs_portafolio.png",dpi=150,facecolor="white"); fig.savefig("post_pension_vs_portafolio.svg",facecolor="white")
