#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LexGuard - 3-Class Hallucination Detection Evaluation (Part 1)
SAFE=Supported, FLAGGED=Refuted, ABSTAIN=Uncertain
"""
import sys, json, time, argparse
from datetime import datetime, timezone
from pathlib import Path

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import requests
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    import seaborn as sns
    sns.set_theme(style="whitegrid", palette="deep")
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False
    plt.style.use("default")

from sklearn.metrics import (
    confusion_matrix, roc_curve, auc, brier_score_loss, log_loss
)

plt.rcParams.update({
    "font.size": 11, "axes.labelsize": 12, "axes.titlesize": 14,
    "xtick.labelsize": 10, "ytick.labelsize": 10, "figure.dpi": 300,
    "savefig.dpi": 300, "axes.grid": True, "grid.alpha": 0.3,
})

SAFE    = "SAFE"
FLAGGED = "FLAGGED"
ABSTAIN = "ABSTAIN"
DECISION_CLASSES = [SAFE, FLAGGED, ABSTAIN]


def draw_heatmap(ax, matrix, annot_matrix=None, xticklabels=None,
                 yticklabels=None, cmap="Blues", fmt=".2f", fontsize=11):
    if HAS_SEABORN:
        kw = {"size": fontsize, "weight": "bold"}
        if annot_matrix is not None:
            sns.heatmap(matrix, annot=annot_matrix, fmt="", cmap=cmap, cbar=True, ax=ax,
                        xticklabels=xticklabels, yticklabels=yticklabels, annot_kws=kw)
        else:
            sns.heatmap(matrix, annot=True, fmt=fmt, cmap=cmap, cbar=True, ax=ax,
                        xticklabels=xticklabels, yticklabels=yticklabels, annot_kws=kw)
    else:
        im = ax.imshow(matrix, cmap=cmap, aspect="auto")
        plt.colorbar(im, ax=ax)
        if xticklabels:
            ax.set_xticks(np.arange(len(xticklabels)))
            ax.set_xticklabels(xticklabels, rotation=0)
        if yticklabels:
            ax.set_yticks(np.arange(len(yticklabels)))
            ax.set_yticklabels(yticklabels)
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                v = annot_matrix[i][j] if annot_matrix is not None else matrix[i, j]
                t = str(v) if annot_matrix is not None else f"{v:{fmt}}"
                ax.text(j, i, t, ha="center", va="center",
                        color="black", weight="bold", fontsize=fontsize)


class ThreeClassEvaluator:
    def __init__(self, api_url="http://localhost:8000/api", output_dir="eval_3class_plots"):
        self.api_url    = api_url.rstrip("/")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.predictions = []

    def load_test_cases(self, file_path):
        path = Path(file_path)
        if not path.exists():
            alt = Path("api-and-sdk") / file_path
            if alt.exists():
                path = alt
            else:
                raise FileNotFoundError(f"Cannot find: {file_path}")
        with open(path, "r", encoding="utf-8") as f:
            cases = json.load(f)
        print(f"[INFO] Loaded {len(cases)} test cases from {path.resolve()}")
        return cases

    def call_check_api(self, text, context, request_id):
        endpoints = [f"{self.api_url}/check"]
        if "/api" not in self.api_url:
            endpoints.append(f"{self.api_url}/api/check")
        else:
            endpoints.append(self.api_url.replace("/api", "") + "/check")
        payload  = {"text": text, "context": context, "request_id": request_id}
        last_err = None
        for ep in endpoints:
            try:
                resp = requests.post(ep, json=payload,
                                     headers={"Content-Type": "application/json"}, timeout=60)
                if resp.status_code == 200:
                    return {"success": True, "data": resp.json(), "endpoint": ep}
                last_err = f"HTTP {resp.status_code}: {resp.text[:200]}"
            except Exception as exc:
                last_err = str(exc)
        return {"success": False, "error": last_err}

    def _classify(self, raw_decision, exp_label):
        """Map raw API decision to 3-class + binary predictions."""
        raw = str(raw_decision).upper()
        if raw in (SAFE, FLAGGED, ABSTAIN):
            pred_dec = raw
        elif raw == "ERROR":
            pred_dec = ABSTAIN
        else:
            pred_dec = SAFE
        exp_dec      = SAFE if exp_label == "Supported" else FLAGGED
        pred_label   = "Supported" if pred_dec == SAFE else "Refuted"
        is_correct_b = (pred_label == exp_label)
        if pred_dec == ABSTAIN:
            is_correct_3 = False
            abs_supp     = (exp_label == "Supported")
            abs_ref      = (exp_label == "Refuted")
        else:
            is_correct_3 = (pred_dec == exp_dec)
            abs_supp = abs_ref = False
        return pred_dec, exp_dec, pred_label, is_correct_b, is_correct_3, abs_supp, abs_ref

    def execute_test_cases(self, test_cases):
        print("\n" + "="*70)
        print("  LIVE API EVALUATION - 70 IT ACT 2000 TEST CASES")
        print("  3-Class Decision: SAFE / FLAGGED / ABSTAIN")
        print("="*70)
        self.predictions = []
        inter = Path("intermediate_3class_results.json")
        for idx, case in enumerate(test_cases, start=1):
            case_id     = case.get("id", idx)
            text        = case.get("text", "")
            context     = case.get("context", "IT Act 2000 verification")
            exp_label   = case.get("expected_label", "Supported")
            category    = case.get("category", "in_kb" if exp_label == "Supported" else "outside_kb")
            subcategory = case.get("subcategory", "general")
            req_id      = f"eval3c_{case_id}_{int(time.time()*1000)}"
            t0 = time.time()
            api_res = self.call_check_api(text, context, req_id)
            latency = round(time.time() - t0, 3)
            if api_res.get("success"):
                data         = api_res["data"]
                decision     = data.get("decision", SAFE)
                trust_index  = float(data.get("trust_index", 0.5))
                claims       = data.get("claims", [])
                sources_list = []
                for claim in claims:
                    sources_list.extend(claim.get("verdict", {}).get("sources", []))
                num_sources = len(sources_list)
                status, err_msg = "SUCCESS", None
            else:
                decision, trust_index = "ERROR", 0.5
                num_sources, sources_list = 0, []
                status, err_msg = "ERROR", api_res.get("error")
            pred_dec, exp_dec, pred_label, is_cb, is_c3, abs_s, abs_r = \
                self._classify(decision, exp_label)
            record = {
                "id": case_id, "section_ref": case.get("section_ref", ""),
                "description": case.get("description", ""), "text": text,
                "category": category, "subcategory": subcategory,
                "expected_label": exp_label, "expected_decision": exp_dec,
                "predicted_decision": pred_dec, "predicted_label": pred_label,
                "trust_index": trust_index, "num_sources": num_sources,
                "sources": sources_list[:5], "is_correct_binary": is_cb,
                "is_correct_3class": is_c3, "abstain_on_supported": abs_s,
                "abstain_on_refuted": abs_r, "latency_seconds": latency,
                "status": status, "error": err_msg,
            }
            self.predictions.append(record)
            mark = "[OK]" if is_cb else "[FAIL]"
            print(f"[{idx:02d}/70] #{case_id:02d} ({category:10s}) | Exp: {exp_label:9s} | "
                  f"Decision: {pred_dec:7s} | Conf: {trust_index:.2f} | {mark} ({latency:.2f}s)")
            if idx % 10 == 0 or idx == len(test_cases):
                with open(inter, "w", encoding="utf-8") as f:
                    json.dump(self.predictions, f, indent=2)
                print(f"   -> [Checkpoint] {idx}/{len(test_cases)} saved")
        return self.predictions

    def load_predictions_from_json(self, json_path):
        path = Path(json_path)
        if not path.exists():
            alt = Path("api-and-sdk") / json_path
            if alt.exists():
                path = alt
            else:
                raise FileNotFoundError(f"Cannot find: {json_path}")
        with open(path, "r", encoding="utf-8") as f:
            saved = json.load(f)
        raw_preds = saved.get("predictions", saved) if isinstance(saved, dict) else saved
        print(f"[INFO] Loaded {len(raw_preds)} saved predictions from {path.resolve()}")
        self.predictions = []
        for p in raw_preds:
            # Handle old format: ground_truth_class=Factual/Hallucination, detected_as_hallucination=bool
            gt = p.get("ground_truth_class", "")
            if gt:
                exp_label = "Supported" if gt == "Factual" else "Refuted"
                is_hall   = p.get("detected_as_hallucination", p.get("detected_class","") == "Hallucination")
                raw_decision = FLAGGED if is_hall else SAFE
            else:
                exp_label    = p.get("expected_label", "Supported")
                raw_decision = p.get("decision") or p.get("predicted_decision") or SAFE
            pred_dec, exp_dec, pred_label, is_cb, is_c3, abs_s, abs_r = \
                self._classify(raw_decision, exp_label)
            rec = {
                **p,
                "expected_label":       exp_label,
                "expected_decision":    exp_dec,
                "predicted_decision":   pred_dec,
                "predicted_label":      pred_label,
                "category":             p.get("category", "in_kb" if p.get("id",0) <= 50 else "outside_kb"),
                "is_correct_binary":    is_cb,
                "is_correct_3class":    is_c3,
                "abstain_on_supported": abs_s,
                "abstain_on_refuted":   abs_r,
                "trust_index":          p.get("trust_index", p.get("confidence", 0.5)),
                "num_sources":          p.get("num_sources", 0),
            }
            self.predictions.append(rec)

    def calculate_metrics(self):
        preds = self.predictions
        n     = len(preds)
        y_true_bin  = np.array([1 if p["expected_label"]  == "Supported" else 0 for p in preds])
        y_pred_bin  = np.array([1 if p["predicted_label"] == "Supported" else 0 for p in preds])
        decisions   = np.array([p["predicted_decision"] for p in preds])
        confidences = np.array([p["trust_index"] for p in preds])
        cm_bin      = confusion_matrix(y_true_bin, y_pred_bin, labels=[0, 1])
        tn, fp, fn, tp = cm_bin.ravel()
        acc_bin  = float((tp + tn) / n)
        prec_bin = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        rec_bin  = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        spec_bin = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
        f1_bin   = 2*prec_bin*rec_bin/(prec_bin+rec_bin) if (prec_bin+rec_bin) > 0 else 0.0
        fpr_val  = float(fp/(fp+tn)) if (fp+tn) > 0 else 0.0
        fnr_val  = float(fn/(tp+fn)) if (tp+fn) > 0 else 0.0
        fpr_arr, tpr_arr, _ = roc_curve(y_true_bin, confidences)
        auc_roc    = float(auc(fpr_arr, tpr_arr))
        opt_idx    = int(np.argmax(tpr_arr - fpr_arr))
        opt_thresh = float(fpr_arr[opt_idx]) if opt_idx < len(fpr_arr) else 0.5
        clipped    = np.clip(confidences, 1e-7, 1 - 1e-7)
        brier      = float(brier_score_loss(y_true_bin, confidences))
        ll         = float(log_loss(y_true_bin, clipped))
        bins_e     = np.linspace(0, 1, 11)
        ece        = 0.0
        for i in range(10):
            lo, hi = bins_e[i], bins_e[i+1]
            mask = (confidences >= lo) & (confidences <= hi if i == 9 else confidences < hi)
            if mask.sum() > 0:
                ece += (mask.sum()/n) * abs(y_true_bin[mask].mean() - confidences[mask].mean())
        cm3      = np.zeros((2, 3), dtype=int)
        exp_idx  = {SAFE: 0, FLAGGED: 1}
        pred_idx = {SAFE: 0, FLAGGED: 1, ABSTAIN: 2}
        for p in preds:
            cm3[exp_idx.get(p["expected_decision"],0), pred_idx.get(p["predicted_decision"],2)] += 1
        n_safe    = int((decisions == SAFE).sum())
        n_flagged = int((decisions == FLAGGED).sum())
        n_abstain = int((decisions == ABSTAIN).sum())
        abstain_rate   = n_abstain / n
        actual_hallucs = [p for p in preds if p["expected_label"] == "Refuted"]
        actual_factuals= [p for p in preds if p["expected_label"] == "Supported"]
        caught_hallucs = [p for p in actual_hallucs if p["predicted_decision"] in (FLAGGED,ABSTAIN)]
        missed_hallucs = [p for p in actual_hallucs if p["predicted_decision"] == SAFE]
        false_alarms   = [p for p in actual_factuals if p["predicted_decision"] in (FLAGGED,ABSTAIN)]
        factual_retd   = [p for p in actual_factuals if p["predicted_decision"] == SAFE]
        h_recall = len(caught_hallucs)/len(actual_hallucs) if actual_hallucs else 0.0
        h_prec   = len(caught_hallucs)/(n_flagged+n_abstain) if (n_flagged+n_abstain)>0 else 0.0
        h_f1     = 2*h_prec*h_recall/(h_prec+h_recall) if (h_prec+h_recall)>0 else 0.0
        miss_r   = len(missed_hallucs)/len(actual_hallucs) if actual_hallucs else 0.0
        fa_r     = len(false_alarms)/len(actual_factuals)  if actual_factuals else 0.0
        fact_r   = len(factual_retd)/len(actual_factuals)  if actual_factuals else 0.0
        avg_tf   = float(np.mean([p["trust_index"] for p in actual_factuals])) if actual_factuals else 0.0
        avg_th   = float(np.mean([p["trust_index"] for p in actual_hallucs]))  if actual_hallucs else 0.0
        src_attr = sum(1 for p in preds if p["num_sources"]>0)/n
        avg_src  = float(np.mean([p["num_sources"] for p in preds]))
        kb_cov   = float(np.mean([1 if p["num_sources"]>0 else 0 for p in actual_factuals])) if actual_factuals else 0.0
        committed    = [p for p in preds if p["predicted_decision"] != ABSTAIN]
        acc_3c_comm  = sum(1 for p in committed if p["is_correct_3class"])/len(committed) if committed else 0.0
        acc_3c_all   = sum(1 for p in preds if p["is_correct_3class"])/n
        abs_on_supp  = sum(1 for p in preds if p["abstain_on_supported"])
        abs_on_ref   = sum(1 for p in preds if p["abstain_on_refuted"])
        def cat_m(subset):
            if not subset:
                return {"count":0,"accuracy":0.0,"safe_pred":0,"flagged_pred":0,"abstain_pred":0,
                        "abstain_rate":0.0,"avg_confidence":0.0,"avg_sources":0.0}
            c  = sum(1 for p in subset if p["is_correct_binary"])
            sc = sum(1 for p in subset if p["predicted_decision"]==SAFE)
            fc = sum(1 for p in subset if p["predicted_decision"]==FLAGGED)
            ac = sum(1 for p in subset if p["predicted_decision"]==ABSTAIN)
            return {"count":len(subset),"correct":c,"incorrect":len(subset)-c,"accuracy":c/len(subset),
                    "safe_pred":sc,"flagged_pred":fc,"abstain_pred":ac,"abstain_rate":ac/len(subset),
                    "avg_confidence":float(np.mean([p["trust_index"] for p in subset])),
                    "avg_sources":float(np.mean([p["num_sources"] for p in subset]))}
        in_kb_preds  = [p for p in preds if p.get("category")=="in_kb"]
        out_kb_preds = [p for p in preds if p.get("category")=="outside_kb"]
        return {
            "binary": {
                "confusion_matrix": {"true_positives":int(tp),"true_negatives":int(tn),"false_positives":int(fp),"false_negatives":int(fn)},
                "accuracy":round(acc_bin,4),"precision":round(prec_bin,4),"recall":round(rec_bin,4),
                "specificity":round(spec_bin,4),"f1_score":round(f1_bin,4),
                "false_positive_rate":round(fpr_val,4),"false_negative_rate":round(fnr_val,4),
                "auc_roc":round(auc_roc,4),"optimal_threshold":round(opt_thresh,4),
                "ece":round(ece,4),"brier_score":round(brier,4),"log_loss":round(ll,4)},
            "three_class": {
                "confusion_matrix_2x3": {
                    "rows":["Expected: SAFE (Supported)","Expected: FLAGGED (Refuted)"],
                    "cols":["Pred: SAFE","Pred: FLAGGED","Pred: ABSTAIN"],
                    "matrix":cm3.tolist()},
                "decision_counts":{"SAFE":n_safe,"FLAGGED":n_flagged,"ABSTAIN":n_abstain},
                "abstain_rate":round(abstain_rate,4),"abstain_on_supported":abs_on_supp,"abstain_on_refuted":abs_on_ref,
                "accuracy_overall":round(acc_3c_all,4),"accuracy_committed_only":round(acc_3c_comm,4)},
            "hallucination": {
                "prevalence_rate":round(len(actual_hallucs)/n,4),
                "detection_rate":round(h_recall,4),"precision":round(h_prec,4),"f1":round(h_f1,4),
                "miss_rate":round(miss_r,4),"false_alarm_rate":round(fa_r,4),"factual_retention":round(fact_r,4),
                "avg_trust_factual":round(avg_tf,4),"avg_trust_hallucinated":round(avg_th,4),
                "discrimination_gap":round(avg_tf-avg_th,4),
                "caught":len(caught_hallucs),"missed":len(missed_hallucs),"false_alarms":len(false_alarms)},
            "faithfulness": {"source_attribution_rate":round(src_attr,4),"avg_sources":round(avg_src,4),"kb_coverage":round(kb_cov,4)},
            "by_category": {"in_kb":cat_m(in_kb_preds),"outside_kb":cat_m(out_kb_preds)},
            "_arrays": {"fpr_arr":fpr_arr.tolist(),"tpr_arr":tpr_arr.tolist(),"auc_roc":auc_roc}}

    def generate_plots(self, metrics):
        print("\n" + "="*70 + "\n  GENERATING 12 VISUALIZATION PLOTS (300 DPI)\n" + "="*70)
        preds = self.predictions
        n     = len(preds)
        y_true = np.array([1 if p["expected_label"]=="Supported" else 0 for p in preds])
        y_pred = np.array([1 if p["predicted_label"]=="Supported" else 0 for p in preds])
        conf   = np.array([p["trust_index"] for p in preds])
        decs   = np.array([p["predicted_decision"] for p in preds])
        bm     = metrics["binary"]
        hm     = metrics["hallucination"]
        tm     = metrics["three_class"]
        ikb    = metrics["by_category"]["in_kb"]
        okb    = metrics["by_category"]["outside_kb"]
        COL    = {SAFE:"#2ca02c",FLAGGED:"#d62728",ABSTAIN:"#ff7f0e"}
        fa     = np.array(metrics["_arrays"]["fpr_arr"])
        ta     = np.array(metrics["_arrays"]["tpr_arr"])
        av     = metrics["_arrays"]["auc_roc"]
        od     = self.output_dir

        def _save(name):
            plt.tight_layout()
            plt.savefig(od/name)
            plt.close()

        # Plot 1: 3-class CM
        fig, ax = plt.subplots(figsize=(8,5))
        cm3   = np.array(tm["confusion_matrix_2x3"]["matrix"])
        annot = np.empty_like(cm3, dtype=object)
        for r in range(2):
            rt = cm3[r].sum()
            for c in range(3):
                pct = cm3[r,c]/rt*100 if rt>0 else 0
                annot[r,c] = f"{cm3[r,c]}\n({pct:.0f}%)"
        draw_heatmap(ax, cm3.astype(float), annot_matrix=annot,
                     xticklabels=["Pred:SAFE","Pred:FLAGGED","Pred:ABSTAIN"],
                     yticklabels=["Exp SAFE\n(Supported)","Exp FLAGGED\n(Refuted)"],cmap="Blues")
        ax.set_title("1. 3-Class Confusion Matrix  (SAFE / FLAGGED / ABSTAIN)",pad=15)
        ax.set_xlabel("Predicted Decision"); ax.set_ylabel("Expected Decision")
        _save("01_3class_confusion_matrix.png")

        # Plot 2: Binary CM
        fig, ax = plt.subplots(figsize=(6.5,5.5))
        cb = confusion_matrix(y_true, y_pred, labels=[1,0])
        an = np.empty_like(cb, dtype=object)
        ll = [["TP","FN"],["FP","TN"]]
        for i in range(2):
            for j in range(2):
                an[i,j] = f"{ll[i][j]}\n{cb[i,j]}\n({cb[i,j]/n*100:.1f}%)"
        draw_heatmap(ax,cb.astype(float),annot_matrix=an,
                     xticklabels=["Pred Supported","Pred Refuted"],
                     yticklabels=["Actual Supported","Actual Refuted"],cmap="Blues")
        ax.set_title("2. Binary Confusion Matrix",pad=15)
        _save("02_binary_confusion_matrix.png")

        # Plot 3: Decision distribution
        fig, axes = plt.subplots(1,2,figsize=(12,5))
        dc   = tm["decision_counts"]
        bv   = list(dc.values())
        b    = axes[0].bar(list(dc.keys()),bv,color=[COL[k] for k in dc],width=0.55,edgecolor="black")
        for bar in b:
            h = bar.get_height()
            axes[0].text(bar.get_x()+bar.get_width()/2,h+0.5,f"{h}\n({h/n*100:.1f}%)",ha="center",weight="bold",fontsize=11)
        axes[0].set_ylim(0,max(bv)*1.3); axes[0].set_ylabel("Cases"); axes[0].set_title("3a. Overall Decision Distribution")
        xr = np.arange(2)
        axes[1].bar(xr-0.25,[ikb["safe_pred"],okb["safe_pred"]],0.25,label="SAFE",color=COL[SAFE],edgecolor="black")
        axes[1].bar(xr,     [ikb["flagged_pred"],okb["flagged_pred"]],0.25,label="FLAGGED",color=COL[FLAGGED],edgecolor="black")
        axes[1].bar(xr+0.25,[ikb["abstain_pred"],okb["abstain_pred"]],0.25,label="ABSTAIN",color=COL[ABSTAIN],edgecolor="black")
        axes[1].set_xticks(xr); axes[1].set_xticklabels(["In-KB\n(Supp)","Outside-KB\n(Ref)"])
        axes[1].set_ylabel("Count"); axes[1].set_title("3b. Decision by Category"); axes[1].legend()
        fig.suptitle("3. Decision Distribution Analysis",fontsize=14,y=1.01)
        plt.tight_layout(); plt.savefig(od/"03_decision_distribution.png",bbox_inches="tight"); plt.close()

        # Plot 4: Metrics Dashboard
        fig, ax = plt.subplots(figsize=(10,5))
        mlbls = ["Accuracy","Precision","Recall","Specificity","F1","AUC-ROC","Halluc\nDetect","Factual\nRetain"]
        mvals = [bm[k] for k in ["accuracy","precision","recall","specificity","f1_score","auc_roc"]] + [hm["detection_rate"],hm["factual_retention"]]
        mcols = ["#4e79a7","#59a14f","#f28e2b","#e15759","#76b7b2","#edc948","#b07aa1","#ff9da7"]
        bars  = ax.bar(mlbls,mvals,color=mcols,width=0.6,edgecolor="black")
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x()+bar.get_width()/2,h+0.02,f"{h:.3f}",ha="center",va="bottom",weight="bold",fontsize=10)
        ax.set_ylim(0,1.15); ax.set_ylabel("Score (0-1)"); ax.set_title("4. Performance Metrics Dashboard",pad=15)
        _save("04_metrics_dashboard.png")

        # Plot 5: ROC Curve
        fig, ax = plt.subplots(figsize=(7,6))
        ax.plot(fa,ta,"#1f77b4",lw=2.5,label=f"ROC (AUC={av:.3f})")
        ax.plot([0,1],[0,1],"gray",ls="--",lw=1.5,label="Random (0.5)")
        oi = int(np.argmax(ta-fa))
        ax.plot(fa[oi],ta[oi],"ro",ms=9,label=f"Opt thresh={bm['optimal_threshold']:.2f}")
        ax.set(xlim=[-0.02,1.02],ylim=[-0.02,1.05],xlabel="FPR",ylabel="TPR")
        ax.set_title("5. ROC Curve",pad=15); ax.legend(loc="lower right")
        _save("05_roc_curve.png")

        # Plot 6: Confidence by decision
        fig, ax = plt.subplots(figsize=(8,5))
        bins6 = np.linspace(0,1,16)
        for dec,col in [(SAFE,COL[SAFE]),(FLAGGED,COL[FLAGGED]),(ABSTAIN,COL[ABSTAIN])]:
            mask = decs==dec
            if mask.sum()>0:
                ax.hist(conf[mask],bins=bins6,alpha=0.65,color=col,label=f"{dec} (n={mask.sum()})",edgecolor="black")
        ax.set(xlabel="Trust Score",ylabel="Frequency"); ax.set_title("6. Confidence by Decision",pad=15); ax.legend()
        _save("06_confidence_by_decision.png")

        # Plot 7: Trust timeline
        fig, ax = plt.subplots(figsize=(12,5))
        ids = np.arange(1,n+1)
        for dec,col,mkr in [(SAFE,"#2ca02c","o"),(FLAGGED,"#d62728","x"),(ABSTAIN,"#ff7f0e","^")]:
            mask = decs==dec
            if mask.sum()>0:
                ax.scatter(ids[mask],conf[mask],c=col,label=dec,marker=mkr,s=55,alpha=0.85)
        ax.axvline(50.5,color="purple",ls="--",lw=1.5,label="In-KB / Outside-KB")
        ax.set(xlabel="Case ID",ylabel="Trust Score",xlim=[0.5,n+0.5],ylim=[-0.05,1.05])
        ax.set_title("7. Trust Score per Case (coloured by decision)",pad=15); ax.legend(loc="lower right")
        _save("07_trust_score_timeline.png")

        # Plot 8: Hallucination summary
        fig, ax = plt.subplots(figsize=(7,5))
        hall_lbl = ["Caught\n(FLAGGED/ABSTAIN)","Missed\n(as SAFE)","False Alarms\n(Factual->Flagged)"]
        hall_val = [hm["caught"],hm["missed"],hm["false_alarms"]]
        b = ax.bar(hall_lbl,hall_val,color=["#2ca02c","#d62728","#ff7f0e"],width=0.5,edgecolor="black")
        for bar in b:
            h = bar.get_height()
            ax.text(bar.get_x()+bar.get_width()/2,max(h+0.15,0.2),str(int(h)),ha="center",weight="bold",fontsize=12)
        ax.set_ylim(0,max(max(hall_val)+2,5)); ax.set_ylabel("Count")
        ax.set_title(f"8. Hallucination Summary  Detect:{hm['detection_rate']*100:.1f}%  Miss:{hm['miss_rate']*100:.1f}%  FalseAlarm:{hm['false_alarm_rate']*100:.1f}%",pad=12)
        _save("08_hallucination_summary.png")

        # Plot 9: Abstain analysis
        fig, ax = plt.subplots(figsize=(6.5,5))
        abs_val = [tm["abstain_on_supported"],tm["abstain_on_refuted"]]
        b = ax.bar(["ABSTAIN on Supported\n(Type-I)","ABSTAIN on Refuted\n(Safe)"],abs_val,
                   color=["#e15759","#76b7b2"],width=0.45,edgecolor="black")
        for bar in b:
            h = bar.get_height()
            ax.text(bar.get_x()+bar.get_width()/2,max(h+0.1,0.15),str(int(h)),ha="center",weight="bold",fontsize=13)
        ax.set_ylim(0,max(max(abs_val)+2,5)); ax.set_ylabel("Count")
        ax.set_title(f"9. ABSTAIN Analysis  Total={tm['decision_counts']['ABSTAIN']}  Rate={tm['abstain_rate']*100:.1f}%",pad=12)
        _save("09_abstain_analysis.png")

        # Plot 10: Accuracy by category
        fig, ax = plt.subplots(figsize=(7,5))
        ca = [ikb["accuracy"],okb["accuracy"]]
        ce = [1-a for a in ca]
        x2 = np.arange(2)
        ax.bar(x2-0.2,ca,0.35,label="Accuracy",color="#4e79a7",edgecolor="black")
        ax.bar(x2+0.2,ce,0.35,label="Error",   color="#e15759",edgecolor="black")
        for i,(a,e) in enumerate(zip(ca,ce)):
            ax.text(i-0.2,a+0.02,f"{a*100:.1f}%",ha="center",weight="bold")
            ax.text(i+0.2,e+0.02,f"{e*100:.1f}%",ha="center",weight="bold")
        ax.set_xticks(x2); ax.set_xticklabels(["In-KB\n(n=50)","Outside-KB\n(n=20)"])
        ax.set_ylim(0,1.15); ax.set_ylabel("Rate"); ax.set_title("10. Accuracy by Category",pad=15); ax.legend()
        _save("10_accuracy_by_category.png")

        # Plot 11: Trust box-plots
        fig, ax = plt.subplots(figsize=(7,5))
        bp = ax.boxplot([conf[y_true==1],conf[y_true==0]],
                        tick_labels=["Supported","Refuted"],patch_artist=True,
                        medianprops=dict(color="black",lw=2))
        for patch,c in zip(bp["boxes"],["#a1d99b","#fc9272"]): patch.set_facecolor(c)
        ax.set_ylabel("Trust Index")
        ax.set_title(f"11. Trust Score by GT  Factual={hm['avg_trust_factual']:.3f}  Halluc={hm['avg_trust_hallucinated']:.3f}  Gap={hm['discrimination_gap']:.3f}",pad=12)
        _save("11_trust_by_ground_truth.png")

        # Plot 12: Running accuracy
        fig, ax = plt.subplots(figsize=(9,5))
        run_acc = np.cumsum([1 if p["is_correct_binary"] else 0 for p in preds]) / np.arange(1,n+1)
        ax.plot(np.arange(1,n+1),run_acc,"#1f77b4",lw=2.5,label="Running Accuracy")
        ax.axhline(bm["accuracy"],color="red",ls="--",label=f"Final={bm['accuracy']:.3f}")
        ax.axvline(50.5,color="purple",ls=":",label="In-KB / Outside-KB")
        ax.set(xlabel="Case #",ylabel="Running Accuracy",xlim=[0.5,n+0.5],ylim=[0,1.05])
        ax.set_title("12. Running Accuracy Over Test Progression",pad=15); ax.legend(loc="lower right")
        _save("12_running_accuracy.png")
        print(f"[OK] All 12 plots saved to: {self.output_dir.resolve()}")

    def save_results(self, metrics, test_file, output_path="evaluation_3class_results.json"):
        payload = {
            "metadata": {
                "evaluation_title": "LexGuard - 3-Class Hallucination Detection Evaluation",
                "statute": "Information Technology Act, 2000",
                "test_file": test_file,
                "total_cases": len(self.predictions),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "decision_classes": DECISION_CLASSES,
            },
            "binary_metrics":        metrics["binary"],
            "three_class_metrics":   metrics["three_class"],
            "hallucination_metrics": metrics["hallucination"],
            "faithfulness_metrics":  metrics["faithfulness"],
            "by_category":           metrics["by_category"],
            "predictions":           self.predictions,
        }
        for p in [Path(output_path), Path("api-and-sdk")/output_path]:
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            print(f"[OK] Results saved to: {p.resolve()}")

    def print_report(self, metrics):
        bm  = metrics["binary"]
        tm  = metrics["three_class"]
        hm  = metrics["hallucination"]
        fa  = metrics["faithfulness"]
        bcat= metrics["by_category"]
        sep = "="*70
        print(f"\n{sep}\n     LEGAL HALLUCINATION DETECTION - EVALUATION REPORT\n     3-CLASS (SAFE / FLAGGED / ABSTAIN) + BINARY\n{sep}")
        dc = tm["decision_counts"]
        print(f"\n[3-CLASS DECISION ACCURACY]")
        print(f"  Decision counts    : SAFE={dc['SAFE']}  FLAGGED={dc['FLAGGED']}  ABSTAIN={dc['ABSTAIN']}")
        print(f"  Abstain Rate       : {tm['abstain_rate']*100:.1f}%  ({tm['abstain_on_supported']} on Supported, {tm['abstain_on_refuted']} on Refuted)")
        print(f"  3-Class Accuracy   : {tm['accuracy_overall']*100:.2f}%  (abstain=wrong)")
        print(f"  Committed Accuracy : {tm['accuracy_committed_only']*100:.2f}%  (excluding ABSTAIN)")
        m = tm["confusion_matrix_2x3"]["matrix"]
        print(f"\n  3-Class Confusion Matrix:")
        print(f"  {'':30s}  {'Pred:SAFE':>10} {'Pred:FLAGGED':>12} {'Pred:ABSTAIN':>12}")
        print(f"  {'Exp SAFE (Supported)':30s}  {m[0][0]:>10} {m[0][1]:>12} {m[0][2]:>12}")
        print(f"  {'Exp FLAGGED (Refuted)':30s}  {m[1][0]:>10} {m[1][1]:>12} {m[1][2]:>12}")
        print(f"\n[BINARY CLASSIFICATION METRICS]")
        print(f"  Accuracy           : {bm['accuracy']*100:.2f}%")
        print(f"  Precision          : {bm['precision']*100:.2f}%  (SAFE -> truly Supported?)")
        print(f"  Recall (TPR)       : {bm['recall']*100:.2f}%  (Supported -> correctly SAFE?)")
        print(f"  Specificity (TNR)  : {bm['specificity']*100:.2f}%  (Refuted -> correctly caught?)")
        print(f"  F1-Score           : {bm['f1_score']:.4f}")
        print(f"  AUC-ROC            : {bm['auc_roc']:.4f}")
        print(f"  Brier Score        : {bm['brier_score']:.4f}  (lower=better)")
        print(f"  ECE                : {bm['ece']:.4f}  (calibration; lower=better)")
        cm = bm["confusion_matrix"]
        print(f"  CM: TP={cm['true_positives']:3d} FN={cm['false_negatives']:3d}  |  FP={cm['false_positives']:3d} TN={cm['true_negatives']:3d}")
        nt = len(self.predictions)
        print(f"\n[HALLUCINATION DETECTION METRICS]")
        print(f"  Prevalence         : {hm['prevalence_rate']*100:.1f}%  ({int(hm['prevalence_rate']*nt)}/{nt} hallucinations)")
        print(f"  Detection Rate     : {hm['detection_rate']*100:.1f}%  (caught by FLAGGED or ABSTAIN)")
        print(f"  Precision          : {hm['precision']*100:.1f}%  (of FLAGGED+ABSTAIN, how many are real halluc?)")
        print(f"  F1                 : {hm['f1']:.4f}")
        print(f"  Miss Rate          : {hm['miss_rate']*100:.1f}%  (hallucinations slipping as SAFE)")
        print(f"  False Alarm Rate   : {hm['false_alarm_rate']*100:.1f}%  (factual wrongly flagged)")
        print(f"  Factual Retention  : {hm['factual_retention']*100:.1f}%  (factual correctly SAFE)")
        print(f"  Trust Gap          : {hm['discrimination_gap']:.4f}  (factual={hm['avg_trust_factual']:.3f} vs halluc={hm['avg_trust_hallucinated']:.3f})")
        print(f"\n[FAITHFULNESS]")
        print(f"  Source Attribution : {fa['source_attribution_rate']*100:.1f}%")
        print(f"  Avg Sources        : {fa['avg_sources']:.2f}")
        print(f"  KB Coverage        : {fa['kb_coverage']*100:.1f}%")
        print(f"\n[CATEGORY BREAKDOWN]")
        ik = bcat["in_kb"]; ok = bcat["outside_kb"]
        print(f"  In-KB (n={ik['count']:2d})     : Acc={ik['accuracy']*100:.1f}% SAFE={ik['safe_pred']} FLAGGED={ik['flagged_pred']} ABSTAIN={ik['abstain_pred']}")
        print(f"  Outside-KB (n={ok['count']:2d}) : Acc={ok['accuracy']*100:.1f}% SAFE={ok['safe_pred']} FLAGGED={ok['flagged_pred']} ABSTAIN={ok['abstain_pred']}")
        print(f"\n{sep}")
        print(f"[DONE] Plots saved to: {self.output_dir.resolve()}")
        print(f"{sep}\n")


def main():
    parser = argparse.ArgumentParser(description="3-Class Evaluation on 70 IT Act Cases")
    parser.add_argument("--api-url",          default="http://localhost:8000/api")
    parser.add_argument("--file",             default="test_cases_70_it_act.json")
    parser.add_argument("--output-dir",       default="eval_3class_plots")
    parser.add_argument("--output-json",      default="evaluation_3class_results.json")
    parser.add_argument("--skip-live",        action="store_true", default=False,
                        help="Skip live API; re-analyse existing results JSON")
    parser.add_argument("--existing-results", default="evaluation_results_70_it_act.json")
    args = parser.parse_args()

    evaluator = ThreeClassEvaluator(api_url=args.api_url, output_dir=args.output_dir)

    if args.skip_live:
        print("[INFO] --skip-live mode: no API calls made.")
        evaluator.load_predictions_from_json(args.existing_results)
    else:
        health_ok = False
        for hu in [f"{args.api_url.rstrip('/')}/health", "http://localhost:8000/health"]:
            try:
                r = requests.get(hu, timeout=5)
                if r.status_code == 200:
                    health_ok = True; print(f"[OK] API server at {hu}"); break
            except Exception:
                continue
        if not health_ok:
            print(f"[WARN] API server at {args.api_url} not reachable.")
            print("[INFO] Start with:  python run_api.py")
            print("[TIP]  Use --skip-live to analyse existing results JSON.")
            sys.exit(1)
        test_cases = evaluator.load_test_cases(args.file)
        evaluator.execute_test_cases(test_cases)

    metrics = evaluator.calculate_metrics()
    evaluator.generate_plots(metrics)
    evaluator.save_results(metrics, test_file=args.file, output_path=args.output_json)
    evaluator.print_report(metrics)


if __name__ == "__main__":
    main()
