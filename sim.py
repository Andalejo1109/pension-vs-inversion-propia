# %% [md] ## Paso 1. Supuestos (todo en pesos/dólares constantes de 2026)
import numpy as np, pandas as pd
SMLMV=1_750_905          # Decreto 1469/2025 (ratificado transitoriamente Decreto 159/2026)
TRM=3_156.32             # TRM 20-oct-2026 (BanRep / SFC); se asume constante en términos reales
G_SML=0.01               # [DEFAULT] SMLMV crece IPC+1% => +1% real al año
IBC_SML=2.0              # cotiza sobre 2 SMLMV
INF_USD=0.025            # [DEFAULT] inflación USA para deflactar retornos del core
W=pd.Series({"SPYG":.31,"SMH":.22,"BRK-B":.20,"IEMG":.20,"VTI":.07})  # core [DEFAULT]
SEED,N,BPS=42,5000,0.0005
CASOS=[dict(sexo=s,inicio=50-a,anios=a) for s in ("Mujer","Hombre") for a in (20,25)]
# %% [md] ## Paso 2. Colpensiones (fórmula art. 34 Ley 100 / art. 32 Ley 2381)
def colpensiones(sexo,anios):
    sem=round(anios*52); edad=57 if sexo=="Mujer" else 62
    req=1000 if sexo=="Mujer" else 1300          # mujeres: 1000 semanas desde 2036 (C-197/23); estas personas se pensionan después de 2036
    gap=edad-50                                   # deja de cotizar a los 50
    # IBL: últimos 10 años indexados por IPC; en SMLMV de la fecha de pensión se erosiona por el +1% real del SMLMV
    k=np.arange(gap,gap+10); s=IBC_SML*np.mean((1+G_SML)**(-k))
    if sem>=req:
        r=65.5-0.5*s+1.5*((sem-req)//50); r=min(r,80)
        mes=max(r/100*s,1.0)                      # en SMLMV; piso 1 SMLMV
        return dict(cumple=True,semanas=sem,req=req,edad=edad,tasa_r=round(r,2),pension_SMLMV=round(mes,3),indemn_SMLMV=0.0)
    # indemnización sustitutiva (art. 37 Ley 100): SBC semanal × semanas × % ponderado (16% aprox.) 
    I=IBC_SML*12/52*sem*0.16
    return dict(cumple=False,semanas=sem,req=req,edad=edad,tasa_r=np.nan,pension_SMLMV=0.0,indemn_SMLMV=round(I,1))
COL=pd.DataFrame([{**c,**colpensiones(c["sexo"],c["anios"])} for c in CASOS]); COL
# %% [md] ## Paso 3. AFP (RAIS, régimen anterior): 11,5% a la cuenta individual
# Referencia histórica (Asofondos, cierre 2024): fondos 14,06% nominal anual desde jul-1995 = 6,8 pts sobre inflación
#   -> real Fisher = 1,1406/(1,1406-0,068) - 1 ≈ 6,3%. Fondo moderado jun-2022–jun-2026: 11,99% nominal (SFC/Colfondos).
#   Contrapunto: la rentabilidad real neta de costos 1995–2016 fue 0,48% (Revista Innovar/SciELO 2019).
# Con la reforma (Ley 2381, desde 1-abr-2027): el componente complementario de ahorro individual solo recibe el IBC que pasa de 2,3 SMLMV.
#   Si cotiza sobre 2 SMLMV, NO hay ahorro obligatorio en AFP después de abr-2027: todo va a Colpensiones.
# Bono pensional: no aplica (persona que empieza a cotizar en 2026, sin tiempos previos en el ISS ni en el sector público).
RR_HIST=round(1.1406/(1.1406-0.068)-1,4)
FIN={"Mujer":89,"Hombre":85}                       # [DEFAULT] edad final simple (renta cierta hasta esa edad)
def a_n(n,i): return (1-(1+i)**-n)/i
def afp(sexo,anios,rr):
    edad=57 if sexo=="Mujer" else 62; gap=edad-50; sal=0.0
    for t in range(anios*12):                      # aporte 11,5% de 2 SMLMV; crece +1% real/año con el SMLMV
        sal=sal*(1+rr)**(1/12)+0.115*IBC_SML*(1+G_SML)**(t/12)
    sal50_cop=sal*SMLMV                            # COP de 2026
    salE_cop=sal50_cop*(1+rr)**gap                 # sin aportar entre 50 y 57/62
    sml_E=SMLMV*(1+G_SML)**(anios+gap)             # SMLMV real en la fecha de la pensión
    sml_50=SMLMV*(1+G_SML)**anios
    out=dict(rent_real=rr,saldo50_COP=round(sal50_cop),saldo50_USD=round(sal50_cop/TRM),saldo_edad_COP=round(salE_cop),saldo_edad_USD=round(salE_cop/TRM))
    for lab,S,ed,sm in (("50",sal50_cop,50,sml_50),("edad",salE_cop,edad,sml_E)):
        n=FIN[sexo]-ed
        rv13=S/(13*a_n(n,0.03)); rv12=S/(12*a_n(n,0.03))          # renta vitalicia simplificada, interés técnico 3% real
        rp=S/(13*a_n(n,rr))                                       # retiro programado (año 1), saldo a la rentabilidad del fondo
        out.update({f"rv13_{lab}_COP":round(rv13),f"rv12_{lab}_COP":round(rv12),f"rp13_{lab}_COP":round(rp),f"rv13_{lab}_SMLMV":round(rv13/sm,3)})
    sem=anios*52; gpm=sem>=1150
    out.update(semanas=sem,pension_anticipada_50=out["rv13_50_SMLMV"]>=1.1,garantia_min_1150sem=gpm,
       resultado_edad=("pensión propia" if out["rv13_edad_SMLMV"]>=1 else ("garantía pensión mínima (1 SMLMV)" if gpm else "devolución de saldos")),
       mesada_edad_SMLMV=out["rv13_edad_SMLMV"],saldo_edad_SMLMV=round(salE_cop/sml_E,1))
    return out
AFP=pd.DataFrame([{**c,**afp(c["sexo"],c["anios"],rr)} for c in CASOS for rr in (0.03,0.04,0.05,RR_HIST)])
assert (AFP.groupby(["sexo","anios"]).saldo50_COP.apply(lambda x: x.is_monotonic_increasing)).all()
AFP
# %% [md] ## Paso 4. Datos reales del core (cache parquet) y validaciones
px=pd.read_parquet("/workspace/retiro-hija/data/precios.parquet")
m=px.resample("ME").last().pct_change(); m["IEMG"]=m["IEMG"].fillna(m["EEM"])   # EEM antes del lanzamiento de IEMG (2012)
R=m[list(W.index)].dropna().iloc[:-1]                                            # quita mes incompleto
assert R.index.is_monotonic_increasing and R.abs().max().max()<1 and not R.isna().any().any()
assert (R.index.to_series().diff().dt.days.dropna()<=31).all()                  # sin huecos
core_real=((1+(R*W).sum(axis=1))/(1+INF_USD)**(1/12)-1).values
print(R.index[0].date(),R.index[-1].date(),len(R),"meses; CAGR real core %.1f%%"%(100*((1+core_real).prod()**(12/len(core_real))-1)))
# %% [md] ## Paso 5. Block bootstrap (12 meses, 5.000 caminos, seed 42) + ventanas históricas
rng=np.random.default_rng(SEED)
def boot(T):
    nb=-(-T//12); st=rng.integers(0,len(core_real)-12,(N,nb))
    return np.stack([np.concatenate([core_real[s:s+12] for s in r])[:T] for r in st])
def dca(ret,ap):
    v=np.zeros(ret.shape[0]); 
    for t in range(ret.shape[1]): v=(v+ap*(1-BPS))*(1+ret[:,t])
    return v
rows=[]
for anios in (20,25):
  B=boot(anios*12+12*12)                        # incluye 12 años extra para crecer hasta 62
  for ap in (100,200):
    v50=dca(B[:,:anios*12],ap)
    g7=v50*np.prod(1+B[:,anios*12:anios*12+84],1); g12=v50*np.prod(1+B[:,anios*12:anios*12+144],1)
    for lab,fix in (("bootstrap core",None),("fijo 5% real",0.05),("fijo 6% real",0.06)):
      if fix is None: x,x57,x62=v50,g7,g12
      else:
        rm=(1+fix)**(1/12)-1; x=np.array([dca(np.full((1,anios*12),rm),ap)[0]]); x57=x*(1+fix)**7; x62=x*(1+fix)**12
      p=lambda a,q: float(np.percentile(a,q))
      rows.append(dict(anios=anios,aporte_usd=ap,escenario=lab,aportado_usd=ap*12*anios,
        P10_50=round(p(x,10)),P50_50=round(p(x,50)),P90_50=round(p(x,90)),
        P50_COP_millones=round(p(x,50)*TRM/1e6,1),P10_COP_millones=round(p(x,10)*TRM/1e6,1),
        ingreso_4pct_mes_P50_COP=round(p(x,50)*0.04/12*TRM),ingreso_4pct_mes_P10_COP=round(p(x,10)*0.04/12*TRM),
        ingreso_4pct_P50_SMLMV=round(p(x,50)*0.04/12*TRM/SMLMV,2),
        P50_a57=round(p(x57,50)),P50_a62=round(p(x62,50))))
INV=pd.DataFrame(rows); INV
# %% [md] ## Paso 6. Ventanas históricas reales (solo hay ventanas de 20 años; no hay de 25 con datos desde 2003)
hist=[]
for ap in (100,200):
  for s in range(0,len(core_real)-240+1,12):
    hist.append(dict(aporte_usd=ap,inicio=str(R.index[s].date()),valor_20a=round(dca(core_real[None,s:s+240],ap)[0])))
HIST=pd.DataFrame(hist); HIST
# %% [md] ## Paso 7. Tabla comparativa y CSV
def mes_cop(sml): return round(sml*SMLMV)
comp=[]
for c in CASOS:
  co=COL[(COL.sexo==c["sexo"])&(COL.anios==c["anios"])].iloc[0]; af=AFP[(AFP.sexo==c["sexo"])&(AFP.anios==c["anios"])&(AFP.rent_real==0.04)].iloc[0]
  for ap in (100,200):
    iv=INV[(INV.anios==c["anios"])&(INV.aporte_usd==ap)&(INV.escenario=="bootstrap core")].iloc[0]
    iv5=INV[(INV.anios==c["anios"])&(INV.aporte_usd==ap)&(INV.escenario=="fijo 5% real")].iloc[0]
    comp.append(dict(sexo=c["sexo"],edad_inicio=c["inicio"],anios=c["anios"],aporte_usd=ap,
      colpensiones=("pensión %s COP/mes desde %d"%(f"{mes_cop(co.pension_SMLMV):,}",co.edad)) if co.cumple else "no cumple semanas: indemnización ≈ %s COP"%f"{mes_cop(co.indemn_SMLMV):,}",
      afp_4pct=af.resultado_edad+(" (%s COP/mes)"%f"{mes_cop(max(af.mesada_edad_SMLMV,1 if 'garant' in af.resultado_edad else af.mesada_edad_SMLMV)):,}" if af.resultado_edad!="devolución de saldos" else " (saldo ≈ %s COP)"%f"{af.saldo_edad_COP:,}"),
      afp_pension_a_50=bool(af.pension_anticipada_50),afp4_saldo50_COP=af.saldo50_COP,afp4_saldo50_USD=af.saldo50_USD,afp4_saldo_edad_COP=af.saldo_edad_COP,
      afp4_rv13_edad_COP=af.rv13_edad_COP,afp4_rp13_edad_COP=af.rp13_edad_COP,afp_tras_abr2027="sin ahorro AFP obligatorio (IBC<=2,3 SMLMV)",
      propia_P50_usd_50=iv.P50_50,propia_P10_usd_50=iv.P10_50,ingreso4_P50_COP=iv.ingreso_4pct_mes_P50_COP,ingreso4_P10_COP=iv.ingreso_4pct_mes_P10_COP,
      ingreso4_fijo5_COP=iv5.ingreso_4pct_mes_P50_COP))
COMP=pd.DataFrame(comp)
for n,d in (("colpensiones",COL),("afp",AFP),("inversion_propia",INV),("ventanas_historicas",HIST),("comparativa",COMP)): d.to_csv(f"{n}.csv",index=False)
assert (INV.P10_50<=INV.P50_50).all() and (INV.P50_50<=INV.P90_50).all()
COMP
# %% [md] ## Paso 8. Gráficos (estilo claro)
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams.update({"font.size":12,"axes.spines.top":False,"axes.spines.right":False,"figure.facecolor":"white"})
# g1: ingreso mensual a los 50 (4%) vs pensión obligatoria
fig,ax=plt.subplots(figsize=(10,5.5)); lab=[];val=[];col=[]
for _,r in INV[INV.escenario!="fijo 6% real"].iterrows():
  lab.append(f"{r.aporte_usd} USD × {r.anios}a\n{'bootstrap P50' if r.escenario=='bootstrap core' else '5% real'}"); val.append(r.ingreso_4pct_mes_P50_COP/1e6); col.append("#2a9d8f" if r.escenario=="bootstrap core" else "#8ab17d")
ax.bar(lab,val,color=col); ax.axhline(SMLMV/1e6,ls="--",color="#e76f51",label="1 SMLMV 2026")
ax.set_ylabel("Millones COP/mes (pesos de 2026)"); ax.set_title("Ingreso sostenible al 4% a los 50 años (complementario)"); ax.legend(); plt.xticks(fontsize=9); plt.tight_layout(); plt.savefig("g1_ingreso_a_los_50.png",dpi=150); plt.close()
# g2: obligatoria
fig,ax=plt.subplots(figsize=(10,5.5)); xs=[];ys=[];cs=[]
for _,c in COL.iterrows():
  xs.append(f"{c.sexo}\n{c.anios}a Colpensiones"); ys.append(c.pension_SMLMV*SMLMV/1e6); cs.append("#264653")
for _,a in AFP[AFP.rent_real==0.04].iterrows():
  v=a.mesada_edad_SMLMV if a.resultado_edad=="pensión propia" else (1.0 if "garant" in a.resultado_edad else 0)
  xs.append(f"{a.sexo}\n{a.anios}a AFP 4%"); ys.append(v*SMLMV/1e6); cs.append("#e9c46a")
ax.bar(xs,ys,color=cs); ax.set_ylabel("Millones COP/mes"); ax.set_title("Pensión obligatoria a los 57/62 cotizando sobre 2 SMLMV\n(0 = no cumple: indemnización o devolución de saldos)"); plt.xticks(fontsize=9); plt.tight_layout(); plt.savefig("g2_pension_obligatoria.png",dpi=150); plt.close()
# g3: distribución saldo a los 50
fig,ax=plt.subplots(figsize=(10,5.5))
for anios,ls in ((20,"-"),(25,"--")):
  for ap,cl in ((100,"#2a9d8f"),(200,"#264653")):
    r=INV[(INV.anios==anios)&(INV.aporte_usd==ap)&(INV.escenario=="bootstrap core")].iloc[0]
    ax.errorbar(f"{ap}USD {anios}a",r.P50_50/1e3,yerr=[[ (r.P50_50-r.P10_50)/1e3],[(r.P90_50-r.P50_50)/1e3]],fmt="o",color=cl,capsize=8,lw=2)
    ax.scatter(f"{ap}USD {anios}a",r.aportado_usd/1e3,marker="_",s=600,color="#e76f51")
ax.set_ylabel("Miles USD reales"); ax.set_title("Saldo a los 50: P10–P50–P90 (raya roja = total aportado)"); plt.tight_layout(); plt.savefig("g3_saldo_P10_P50_P90.png",dpi=150); plt.close()
# g4: a los 50 vs 57 vs 62
fig,ax=plt.subplots(figsize=(10,5.5)); d=INV[INV.escenario=="bootstrap core"]; x=np.arange(len(d)); w=.27
ax.bar(x-w,d.P50_50/1e3,w,label="a los 50",color="#2a9d8f"); ax.bar(x,d.P50_a57/1e3,w,label="a los 57 (sin aportar más)",color="#e9c46a"); ax.bar(x+w,d.P50_a62/1e3,w,label="a los 62",color="#e76f51")
ax.set_xticks(x,[f"{a}USD {y}a" for a,y in zip(d.aporte_usd,d.anios)]); ax.set_ylabel("Miles USD reales (P50)"); ax.set_title("¿Retirarse a los 50 o esperar a 57/62?"); ax.legend(); plt.tight_layout(); plt.savefig("g4_50_vs_57_62.png",dpi=150); plt.close()
print("ok gráficos")
# %% [md] ## Paso 9. Gráfico AFP: saldo y mesada vs 1 SMLMV
fig,(a1,a2)=plt.subplots(1,2,figsize=(13,5.5)); d=AFP[AFP.sexo=="Hombre"]
for anios,mk in ((20,"o-"),(25,"s--")):
  x=d[d.anios==anios]; a1.plot(x.rent_real*100,x.saldo50_COP/1e6,mk,color="#2a9d8f",label=f"{anios}a, a los 50"); a1.plot(x.rent_real*100,x.saldo_edad_COP/1e6,mk,color="#e76f51",label=f"{anios}a, a los 62 sin aportar")
for sx,cl in (("Mujer","#9b5de5"),("Hombre","#264653")):
  for anios,mk in ((20,"o-"),(25,"s--")):
    x=AFP[(AFP.sexo==sx)&(AFP.anios==anios)]; a2.plot(x.rent_real*100,x.rv13_edad_COP/1e6,mk,color=cl,label=f"{sx} {anios}a ({57 if sx=='Mujer' else 62})")
a2.axhline(SMLMV/1e6,ls="--",color="#e76f51",label="1 SMLMV 2026 (en la fecha de pensión será ~1,01^años mayor)")
a1.set_title("Saldo AFP (millones COP 2026)");a1.set_xlabel("Rentabilidad real %");a1.legend(fontsize=9)
a2.set_title("Mesada renta vitalicia simplificada (13/año)");a2.set_xlabel("Rentabilidad real % (6,3% = histórico Asofondos)");a2.set_ylabel("Millones COP/mes");a2.legend(fontsize=8)
plt.suptitle("AFP cotizando sobre 2 SMLMV (régimen anterior; tras abr-2027 no aplica a 2 SMLMV)");plt.tight_layout();plt.savefig("g5_afp_saldo_mesada.png",dpi=150);plt.close();print("ok g5")
