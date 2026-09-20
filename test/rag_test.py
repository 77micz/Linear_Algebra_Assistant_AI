
# ------------------------ 测试 RAG 效果 ------------------------
import json


from func.retriever import Retriever
import re




# ------------------------ 全局变量 ------------------------

# 测试集文件路径
input_path="test_set.json"

# 测试向量库
retriever = Retriever(
    "../data/vector_db", # 向量库路径
)

# 测试集合
COLLECTION_NAME = "linear_algebra"


# 测试报告输出路径
output_path="test_report.json"


# 存储每个prompt的平均准确率@k
average_precision_atk=[]

# ------------------------ 评估函数 ------------------------




def calculate_precision_at_k(results:list[dict], expected_chunks:list)->float:
    """
    计算一个问题的准确率@k

    :param results: 检索结果列表
    :param expected_chunks: 预期的检索结果列表

    :return: 一个问题的准确率@k
    """
    return sum([1 for result in results if result["id"] in expected_chunks])/len(results)







def calculate_recall_at_k(results:list[dict], expected_chunks:list)->float:
    """
    计算一个问题的召回率@k

    :param results: 检索结果列表
    :param expected_chunks: 预期的检索结果列表

    :return: 一个问题的召回率@k
    """
    return sum([1 for result in results if result["id"] in expected_chunks])/len(expected_chunks)






def calculate_avg_precision_at_k(prompt:str,results:list[dict], expected_chunks:list)->float:
    """
    计算一个问题的平均准确率@k

    :param prompt: 问题的prompt
    :param results: 检索结果列表
    :param expected_chunks: 预期的检索结果列表

    :return: 一个问题的平均准确率@k
    """
    precision_at_k=[]
    # 遍历结果集，计算当前文档是相关文档的准确率
    for i,result in enumerate(results):
        if result["id"] in expected_chunks:
            precision_at_k.append(1.0/(i+1))

    # 把结果保存到全局变量
    average_precision_atk.append(
        {
            "prompt":prompt,
            "avg_precision_at_k":sum(precision_at_k)/len(precision_at_k) if len(precision_at_k)>0 else 0.0,
        }
    )
    return sum(precision_at_k)/len(precision_at_k) if len(precision_at_k)>0 else 0.0




def map_at_k()->float:
    """
    计算典型问题的平均平均准确率@k

    :return: 典型问题的平均平均准确率@k
    """
    _map=0.0
    for avg in average_precision_atk:
        _map+=avg["avg_precision_at_k"]
    return _map/len(average_precision_atk)




def mrr_at_k(questions_recalls:list[list[dict]], test_set:list[dict])->float:
    """
    MRR: Mean Reciprocal Rank 平均倒数排名
    计算典型问题的平均MRR
    :param questions_recalls: 检索结果列表
    :param test_set: 测试集数据列表

    for test,result in zip(test_set,questions_recalls):
        if test["id"] in result:
            _mrr+=1.0/(result.index(test)+1)

    :return: 典型问题的平均MRR
    """
    # 计算每个问题的RR
    each_rr=[]
    for test,results in zip(test_set,questions_recalls):
        for i,result in enumerate(results):
            if result["id"] in test["expected_chunks"]:
                each_rr.append(1.0/(i+1))
                break

    return sum(each_rr)/len(each_rr) if len(each_rr)>0 else 0.0




def recall_summary(results:list[dict], expected_chunks:list)->list[list[dict]]:
    """
    召回汇总

    :param results: 检索结果列表
    :param expected_chunks: 预期的检索结果列表
    """
    # 命中的id
    hit=[]
    # 遗漏的id
    miss=[]
    # 实际召回的id
    actual_recall=[result['id'] for result in results]

    for chunk in expected_chunks:
        if chunk in actual_recall:
            hit.append(chunk)
        else:
            miss.append(chunk)

    # 输出命中和遗漏的id
    print(f"命中: {hit}")
    print(f"遗漏: {miss}")
    print(f"实际召回: {actual_recall}")

    return [hit,miss,actual_recall]









def calculate_concept_coverage(results:list[dict], key_concepts:list)->float:
    """
    计算概念覆盖率
    正则表达式匹配期望包含的概念，计算概念覆盖率

    :param results: 检索结果列表
    :param key_concepts: 关键概念

    :return: 概念覆盖率
    """

    # 拼接所有检索结果的 content
    content=" ".join([result["content"] for result in results])

    # 计算检索结果中包含预期结果的个数占比
    num=0
    for key_concept in key_concepts:
        # 匹配键概念
        if re.search(key_concept, content,re.DOTALL):
            num+=1
    return num/len(key_concepts)





def average_concept_coverage(questions_recalls:list[list[dict]], test_set:list[dict])->float:
    """
    计算平均概念覆盖率

    :param questions_recalls: 检索结果列表
    :param test_set: 测试集数据

    :return: 平均概念覆盖率
    """
    return sum([calculate_concept_coverage(result, test["key_concepts"]) for test,result in zip(test_set,questions_recalls)])/len(test_set)




















# ------------------------ 主函数 ------------------------



"""
结构：
{
summary:{
    "avg_recall_at_k":0.0,
    "avg_mrr":0.0,
    "avg_concept_coverage":0.0,
    },
    "questions":[
        {
            "question":"问题1",
            "payloads":[],
            "recall_at_k":0.0,
            "mrr":0.0,
            "concept_coverage":0.0,
        },
        {
            "question":"问题2",
            "payloads":[],
            "recall_at_k":0.0,
            "mrr":0.0,
            "concept_coverage":0.0,
            },
            ]
    
}
"""
def test_rag(file_path:str, report_path:str=output_path):
    """
    测试RAG效果

    :param file_path: 测试集文件路径
    :param report_path: 测试报告输出路径
    :return: 测试集数据
    """

    # 打开文件
    with open(file_path,"r",encoding="utf-8") as f:
        # 加载测试集数据
        test_set=json.load(f)

        # 存储每个问题的检索结果
        questions_recalls=[]

        # 存储测试报告
        report={}

        # 存储问题
        questions=[]





        # 循环遍历
        for test in test_set:

            # 存储问题
            one={}


            # 提取问题
            question=test["question"]
            one["question"]=question

            # 根据问题检索向量库
            results = retriever.hybrid_search(question, collection_name=COLLECTION_NAME,rerank=False)


            # 获取payload
            results_payload=[result.payload for result in results]


            # 获取分数列表
            scores=[result.score for result in results]

            # 分别存储到payloads中
            for i,result in enumerate(results_payload):
                result["score"]=float(scores[i])
            one["payloads"]=results_payload





            print("-"*30)

            print(f"检索结果: {results_payload}")



            # 存储检索结果
            questions_recalls.append(results_payload)



            # 打印问题
            print(f"问题: {question}")


            print("="*30)

            # 召回汇总
            hit,miss,actual_recall=recall_summary(results_payload, test["expected_chunks"])
            one["hit"]=hit
            one["miss"]=miss


            # 计算准确率
            precision_at_k=calculate_precision_at_k(results_payload, test["expected_chunks"])
            print(f"准确率@k: {precision_at_k:.4f}")
            one["precision_at_k"]=precision_at_k



            # 计算召回率@k
            recall_at_k=calculate_recall_at_k(results_payload, test["expected_chunks"])
            print(f"召回率@k: {recall_at_k:.4f}")
            one["recall_at_k"]=recall_at_k


            # 计算average_precision_at_k
            average_precision_at_k=calculate_avg_precision_at_k(question, results_payload, test["expected_chunks"])
            print(f"平均准确率@k: {average_precision_at_k:.4f}")
            one["average_precision_at_k"]=average_precision_at_k


            questions.append(one)


        print("="*30)


        summary={}



        # 计算MAP
        _map=map_at_k()
        print(f"MAP: {_map:.4f}")
        summary["MAP"]=_map

        # 计算MRR
        mrr=mrr_at_k(questions_recalls, test_set)
        print(f"MRR: {mrr:.4f}")
        summary["MRR"]=mrr


        # 存储摘要
        report["summary"]=summary

        # 存储问题
        report["questions"]=questions

        # 保存报告
        with open(report_path,"w",encoding="utf-8") as file:
            json.dump(report,file,ensure_ascii=False,indent=4)









# ------------------------ 测试 ------------------------
if __name__ == "__main__":
    test_rag(input_path)
    # 释放资源
    retriever.release()












