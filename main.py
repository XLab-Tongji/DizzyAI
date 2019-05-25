from TimeNLP import TimeNormalizer
from extractor import Extractor
from LeaveMessage import LeaveMessage
# from name import NameMatcher
import re
import arrow
import json
from stanfordcorenlp import StanfordCoreNLP
from nltk.tree import ParentedTree
from get_reason import find_reason, preprocess



message = LeaveMessage()
# nm = NameMatcher()
tn = TimeNormalizer()
ex = Extractor()


def get_start_and_end_and_duration(sentence):
    s_time = message.startDate
    e_time = message.endDate
    duration = message.duration
    pos, res = tn.parse(target=sentence)
    # print(pos)
    # print(res)
    res = json.loads(res)

    try:
        if res['type'] == "timedelta":
            duration = res['timedelta']
            # print(duration)

        elif res['type'] == "timespan":
            s_time = res['timespan'][0]
            e_time = res['timespan'][1]
        elif res['type'] == "timestamp":
            s_time = res['timestamp']
            # print(s_time)

        if s_time is not None and duration is not None and e_time is None:
            t_days = int(duration.split()[0])
            t_days -= 1
            e_time = arrow.get(s_time).shift(days=+t_days).format('YYYY-MM-DD HH:mm:ss')
        elif s_time is not None and duration is not None and e_time is not None:
            t_days = int(duration.split()[0])
            t_days -= 1
            if e_time != arrow.get(s_time).shift(days=+t_days).format('YYYY-MM-DD HH:mm:ss'):
                s_time = None
                e_time = None
                duration = None
                print("请重新输入请假时间")

        return (s_time, e_time, duration)
    except:
        return (s_time, e_time, duration)


def get_type(sentence):
    affairs = re.search(r'(.*)事(.*?)假(.*).*', sentence, re.M | re.I)
    sick = re.search(r'(.*)病(.*?)假(.*).*', sentence, re.M | re.I)
    marriage = re.search(r'(.*)婚(.*?)假(.*).*', sentence, re.M | re.I)
    if affairs:
        return "事假"
    elif sick:
        return "病假"
    elif marriage:
        return "婚假"
    else:
        return None


def get_examinPerson(sentence):
    name = ex.extract_name(sentence)
    # name = nm.match(sentence)
    # print(name)
    return name


def get_email(sentence):
    email = ex.extract_email(sentence)
    return email


def ask(message):
    if message.type is None:
        return "请输入请假类型"

    if message.startDate is None and message.endDate is None and message.duration is None:
        return "请输入请假时间"
    elif message.startDate is not None and message.endDate is None and message.duration is None:
        return "你想请几天假"
    elif message.startDate is None and message.endDate is None:
        return "请输入请假的开始或结束时间"

    if message.examinePerson is None:
        return "请输入您的审批人姓名"

    if message.email is None:
        return "请输入抄送邮箱"

    return None


def do_ask_for_leave(sentence):
    matchObj = re.search(r'(.*)请(.*?)假(.*).*', sentence, re.M | re.I)
    return matchObj


def ask_for_leave(sentence):
    while True:
        if message.type is None:
            message.type = get_type(sentence)

        if message.startDate is None or message.endDate is None:
            message.startDate, message.endDate, message.duration = get_start_and_end_and_duration(sentence)

        if message.examinePerson is None:
            message.examinePerson = get_examinPerson(sentence)

        if message.email is None:
            message.email = get_email(sentence)

        question = ask(message)
        if question is not None:
            print(question)
            sentence = input()
            continue
        else:
            break

        # print("确认吗？")
        # sentence = input()
        # if "确认" in sentence:
        #     break
        # elif "不" in sentence:
        #     message.duration = None
        #     message.type = None
        #     message.email = None
        #     message.endDate = None
        #     message.examinePerson = None
        #     message.startDate = None
        #     message.reason = None
    return message


def main():
    with StanfordCoreNLP(r'D:\corenlp\stanford-corenlp-full-2018-10-05', lang='zh', memory='4g', quiet=True,) as nlp:
        nlp.parse("test")
        while True:
            print("请输入")
            sentence = input()
            if do_ask_for_leave(sentence):
                message = ask_for_leave(sentence)

                while True:
                    if len(message.reason) == 0:
                        processed = preprocess(sentence)
                        splits = re.compile("[,，。,]").split(processed)
                        results = [nlp.parse(s) for s in splits]
                        trees = [ParentedTree.fromstring(result) for result in results]
                        final_result = find_reason(trees)
                        message.reason = "".join(final_result)
                        # print(message.reason)
                        # print(len(message.reason))
                        if len(message.reason) == 0:
                            print("请输入请假理由")
                            sentence = input()
                        else:
                            break

                print("确认吗？")
                sentence = input()
                if "确认" in sentence:
                    print("\n开始时间：", message.startDate,
                          "\n结束时间：", message.endDate,
                          "\n请假长度：", message.duration,
                          "\n请假类型：", message.type,
                          "\n审核人：", message.examinePerson,
                          "\n抄送邮箱：", message.email,
                          "\n请假理由：", message.reason)
                    break
                elif "不" in sentence:
                    message.duration = None
                    message.type = None
                    message.email = None
                    message.endDate = None
                    message.examinePerson = None
                    message.startDate = None
                    message.reason = ""

            print("你要做什么呢")


main()
