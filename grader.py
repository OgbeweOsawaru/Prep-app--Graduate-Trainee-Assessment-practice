from schemas import Score,Question,ReviewItem
import config
def make_score(correct, total)-> Score:
    if total == 0:
        percent = 0.0
    else:
        percent = round(100 * correct / total, 1)
    return Score(correct=correct, total=total, percent=percent)
def grade(questions:list[Question], answers:dict):
    review_list:list[ReviewItem]=[]
    correct = {section: 0 for section in config.BLUEPRINT}
    totals = {section: 0 for section in config.BLUEPRINT}
    for question in questions:
        if question.answer== answers.get(question.id):
            correct[question.section]+=1
        review=ReviewItem(
        id=question.id,
        section=question.section,
        question=question.question,
        options=question.options,
        your_answer=answers.get(question.id),
        correct_answer=question.answer,
        passage=question.passage,
        is_correct= question.answer== answers.get(question.id),
        explanation= question.explanation)
        review_list.append(review)
        """review = ReviewItem(
        **question.model_dump(exclude={"answer"}),
        your_answer=given,
        correct_answer=question.answer,
        is_correct=is_correct,
        )"""    
        totals[question.section]+=1
    overall_total=sum(totals.values())
    overall_correct=sum(correct.values())
    section_score={}
    for (k,v), (k2,v2) in zip(correct.items(), totals.items()):
        section_score[k]=make_score(v,v2)
    return make_score(overall_correct,overall_total),section_score,review_list

if __name__ == "__main__":
    from bank import load_bank

    bank = load_bank()
    questions = bank[:5]
    answers = {q.id: q.answer for q in questions[:3]}

    overall, sections, review = grade(questions, answers)
    print(overall)
    print(sections)
    for item in review:
        print(item.id, item.your_answer, item.correct_answer, item.is_correct)
