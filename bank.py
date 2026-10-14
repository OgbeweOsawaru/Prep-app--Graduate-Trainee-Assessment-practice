import config
from schemas import Options,Question
import csv
class BankError(Exception):
    pass
REQUIRED_COLUMNS=['id', 'section', 'passage', 'question', 'option_a', 'option_b', 'option_c', 'option_d', 'option_e', 'answer', 'explanation']

def load_questions(path=config.CSV_PATH)-> list[dict]:
    with open(path, mode='r', newline='', encoding='utf-8-sig') as csvfile:
        # Create DictReader object
        reader = csv.DictReader(csvfile)
        header=reader.fieldnames or []
        missing=set(REQUIRED_COLUMNS)-set(header)
        if missing:
            raise BankError(f"Missing columns in {path}: {sorted(missing)}")
        questions=[line for line in reader]
        warnings,errors=validate_rows(questions)
        if warnings:
            print ("\n".join(warnings))
        if errors :
            raise BankError("\n".join(errors))
        for row in questions:
            row["id"] = row["id"].strip()
            row["section"]= row["section"].strip().lower()
            row["answer"]= row["answer"].strip().lower()
            row["passage"]=row["passage"].strip() or None
        
        return questions

def validate_rows(rows):
    errors=[]
    warnings=[]
    seen_ids=set()
    for row_number,row in enumerate(rows,start=2):
        row_id = row["id"].strip()
        section = row["section"].strip().lower()
        answer = row["answer"].strip().lower()
        question=row["question"].strip().lower()
        if row_id=="":
            errors.append(f"Row {row_number}: ID is empty")
        if row_id in seen_ids:
            errors.append(f"Row {row_number}: ID is duplicated")
        if section not in config.BLUEPRINT:
            errors.append(f"Row {row_number}: {section} Section is not in Blueprint")
        if question =="":
            errors.append(f"Row {row_number}: Question is empty")
        if row["option_a"].strip()=="" or row["option_b"].strip()=="" or row["option_c"].strip()=="" or row["option_d"].strip()=="" or row["option_e"].strip()=="":
            errors.append(f"Row {row_number}: An option is empty")
        if answer not in ["a","b","c","d","e"]:
            errors.append(f"Row {row_number}: Answer is not in options")
        seen_ids.add(row_id)
    return warnings, errors

def row_to_question(row:dict)->Question:
    option = Options(a=row["option_a"], b=row["option_b"], c=row["option_c"], d=row["option_d"],e=row["option_e"])

    return Question(
        id=row["id"],
        section=row["section"],
        passage=row["passage"],
        question=row["question"],
        options=option,
        answer=row["answer"],
        explanation=row["explanation"],
    )
def load_bank()->list[Question]:
    return [row_to_question(row) for row in load_questions()]
    """bank=load_questions()
    load=[]
    for row in bank:
        load.append(row_to_question(row))
    return load"""
if __name__ == "__main__":
    a=load_bank()
    print(a[0].to_public().model_dump())
    print("answer" in a[0].to_public().model_dump())
        
   

            