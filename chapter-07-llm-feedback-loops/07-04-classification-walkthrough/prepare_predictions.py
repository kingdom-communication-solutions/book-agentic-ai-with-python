"""Optional author baseline reproduction. Not needed to run the report project.
Run in the preparation environment documented in dataset-notes.md.
Writes to a required separate --output folder; does not alter the learner inputs.
"""
from pathlib import Path
import argparse,csv,json,hashlib
import sklearn,numpy,scipy
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression


def prepare(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    data=load_breast_cancer()  # Bundled public dataset, no network download.
    train,test=train_test_split(list(range(len(data.target))),test_size=.25,
                               random_state=42,stratify=data.target)
    model=make_pipeline(StandardScaler(),LogisticRegression(
        solver="liblinear",max_iter=2000,random_state=42))
    model.fit(data.data[train],data.target[train])
    indices=sorted(test)
    predicted=model.predict(data.data[indices])
    rows=[{"sample_id":f"sample-{index:04d}",
           "reference_label":str(data.target_names[data.target[index]]),
           "predicted_label":str(data.target_names[prediction])}
          for index,prediction in zip(indices,predicted)]
    path=output/"predictions.csv"
    with path.open("w",newline="") as file:
        writer=csv.DictWriter(file,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    correct=sum(r["reference_label"]==r["predicted_label"] for r in rows)
    malignant=[r for r in rows if r["reference_label"]=="malignant"]
    detected=sum(r["predicted_label"]=="malignant" for r in malignant)
    counts={"evaluated_samples":len(rows),"correct_predictions":correct,
            "malignant_samples":len(malignant),"correct_malignant":detected,
            "missed_malignant":len(malignant)-detected,
            "benign_samples":len(rows)-len(malignant),
            "benign_predicted_malignant":sum(r["reference_label"]=="benign" and r["predicted_label"]=="malignant" for r in rows)}
    result={"counts":counts,"accuracy":round(correct/len(rows),4),
            "malignant_recall":round(detected/len(malignant),4),
            "missed_malignant":len(malignant)-detected,
            "prediction_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
            "preparation":{"dataset":"UCI Breast Cancer Wisconsin (Diagnostic)",
             "doi":"10.24432/C5DW2B","license":"CC BY 4.0",
             "loader_label_mapping":{"0":"malignant","1":"benign"},
             "train_samples":len(train),"test_samples":len(test),
             "test_size":.25,"stratified":True,"random_state":42,
             "pipeline":"StandardScaler fitted on training data only; LogisticRegression(solver=liblinear, max_iter=2000, random_state=42)",
             "versions":{"scikit-learn":sklearn.__version__,"numpy":numpy.__version__,"scipy":scipy.__version__}}}
    (output/"reference-results.json").write_text(json.dumps(result,indent=2)+"\n")
    return result

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--output",required=True)
    args=parser.parse_args();print(json.dumps(prepare(args.output),indent=2))
