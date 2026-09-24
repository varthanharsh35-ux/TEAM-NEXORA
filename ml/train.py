"""Train a small supervised character-ngram classifier, not a large language model.
Independent hand-authored holdout phrases are never used in fitting or augmentation.
"""
from pathlib import Path
import json,csv,random,joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report,accuracy_score,f1_score
ROOT=Path(__file__).resolve().parents[1]
def read(file):
 rows=[]
 for line in (ROOT/'data'/file).read_text(encoding='utf8').splitlines():
  label,phrases=line.split('\t')
  for phrase in phrases.split('|'):rows.append((phrase,label))
 return rows
train=read('business_seed.tsv');test=read('business_holdout.tsv');rng=random.Random(26091)
aug=[]
for phrase,label in train:
 aug.append((phrase,label))
 if phrase.isascii():
  for prefix in ['I want to start ','rural business ','small ','']:
   aug.append((prefix+phrase,label))
  if len(phrase)>8:
   i=rng.randrange(1,len(phrase)-1);aug.append((phrase[:i]+phrase[i+1:],label))
model=Pipeline([('tfidf',TfidfVectorizer(analyzer='char',ngram_range=(2,5),sublinear_tf=True)),('classifier',LogisticRegression(C=12,max_iter=1200,class_weight='balanced',random_state=26091))])
model.fit([r[0] for r in aug],[r[1] for r in aug])
pred=model.predict([r[0] for r in test]);truth=[r[1] for r in test]
metrics={'model':'TF-IDF character 2-5 grams + multinomial logistic regression','seed':26091,'training_base':len(train),'training_augmented':len(aug),'holdout':len(test),'accuracy':accuracy_score(truth,pred),'macro_f1':f1_score(truth,pred,average='macro'),'per_class':classification_report(truth,pred,output_dict=True,zero_division=0),'limitations':'Small synthetic authored dataset; holdout is independent wording, not an external representative survey. These metrics do not measure feasibility accuracy, location accuracy or LLM quality.','errors':[{'text':r[0],'expected':r[1],'predicted':str(p)} for r,p in zip(test,pred) if r[1]!=p]}
(ROOT/'models').mkdir(exist_ok=True)
joblib.dump(model,ROOT/'models/business_classifier.joblib')
(ROOT/'models/metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding='utf8')
with (ROOT/'data/business_training.csv').open('w',encoding='utf8',newline='') as f:
 w=csv.writer(f);w.writerow(['text','category','split']);w.writerows((p,l,'train') for p,l in aug);w.writerows((p,l,'test') for p,l in test)
print(json.dumps({k:metrics[k] for k in ['training_base','training_augmented','holdout','accuracy','macro_f1','errors']},ensure_ascii=False))
