#!/usr/bin/env python3
"""
LingFlow MCP Server - 工具中文名别名映射（雅正版）

灵系命名雅正 - 众智混元，万法灵通
修订说明：参以经史子集、诗赋韵语，务求音谐意雅
"""

from typing import Dict, Optional

# 工具中文名到英文名的映射（雅正版）
TOOL_ALIASES_CN_TO_EN: Dict[str, str] = {
    # 技能系统
    "灵艺": "list_skills",      # 六艺之典，技能为君子之能
    "灵行": "run_skill",        # 行健之义，执行力为首

    # 代码审查
    "灵鉴": "review_code",      # 鉴有照察品评之义

    # 情报系统
    "灵探": "get_github_trends",  # 探有探索采撷之意
    "灵觉": "get_npm_trends",     # 先知觉后知，感知趋势

    # 工作流管理
    "灵流": "list_workflows",           # 流喻流程，如水流通
    "灵运": "run_workflow",             # 运为运转推行
    "灵踪": "get_workflow_status",      # 踪谓踪迹，追踪状态

    # 需求管理
    "灵愿": "create_requirement",       # 愿即愿望，对应需求
    "灵览": "get_requirement",          # 玄览之语，观照需求
    "灵新": "update_requirement",       # 日新之训，更新迭代
    "灵录": "list_requirements",        # 录即记录，条目清晰
    "灵联": "link_requirement_to_branch",  # 联缀之意，贯通串联

    # 任务管理
    "灵讯": "get_task_status",  # 讯即讯息问询
    "灵任": "list_tasks",       # 任重道远，担责在肩

    # 测试运行
    "灵验": "run_tests",               # 验即检验验证
    "灵覆": "get_coverage",            # 曲成万物，覆盖无遗
    "灵书": "generate_test_report",    # 书为文书报告

    # 运维监控
    "灵脉": "get_health_status",  # 脉为生命之征
    "灵量": "get_metrics",       # 斗斛以量，精确度量
    "灵警": "detect_anomaly",    # 警即警示警报
}

# 工具英文名到中文名的映射
TOOL_ALIASES_EN_TO_CN: Dict[str, str] = {
    v: k for k, v in TOOL_ALIASES_CN_TO_EN.items()
}

# 工具描述映射（含国学释义）
TOOL_DESCRIPTIONS_CN: Dict[str, str] = {
    "灵艺": "列举灵巧技艺（取《周礼》六艺之典，技能为君子之能）",
    "灵行": "施展灵巧技能（用《易》行健之义，执行力为首）",
    "灵鉴": "灵慧鉴别代码（鉴有照察品评之义，极当）",
    "灵探": "灵妙探索GitHub（探有探索采撷之意，合于数据采集）",
    "灵觉": "灵敏感知npm（先知觉后知，感知趋势，启迪智慧）",
    "灵流": "查看灵妙流转（流喻流程，如水之流通，自然贴切）",
    "灵运": "灵动运转流程（运为运转推行，恰符工作流运行）",
    "灵踪": "追踪灵迹状态（踪谓踪迹，追踪状态，形象）",
    "灵愿": "记录灵巧心愿（愿即愿望，对应需求，文雅）",
    "灵览": "灵明观照需求（化玄览之语，观照需求，洞若观火）",
    "灵新": "灵活更新需求（本日新之训，更新迭代，生生不息）",
    "灵录": "汇总所有心愿（仿应录之实，条目清晰，一览无余）",
    "灵联": "建立灵妙关联（取联缀之意，串联需求与代码，贯若珠玑）",
    "灵讯": "查询灵妙讯息（讯为讯息问询，合于查询状态）",
    "灵任": "汇总灵巧事务（引任重道远之慨，任务虽繁，担责在肩）",
    "灵验": "灵巧验证功能（验即检验验证，贴切测试之旨）",
    "灵覆": "灵妙覆盖全面（法曲成万物之量，覆盖率广，无遗无漏）",
    "灵书": "灵明书录报告（书为文书报告，雅驯）",
    "灵脉": "诊断灵妙脉络（脉即脉络，健康检查，中医底蕴）",
    "灵量": "灵明精准计数（援斗斛以量之喻，指标精确，可度可量）",
    "灵警": "灵敏警示异常（警为警戒警报，合于异常检测）",
}

# 国学典故映射
TOOL_ALLUSIONS: Dict[str, str] = {
    "灵艺": "《周礼·保氏》'养国子以道，乃教之六艺' - 艺为君子之能",
    "灵行": "《易·乾》'君子以成德为行' - 行乃践履之功",
    "灵鉴": "《诗·大雅》'殷鉴不远' - 鉴即明察",
    "灵探": "《论语·季氏》'见不善如探汤' - 探为探取",
    "灵觉": "《孟子·万章上》'先知觉后知' - 觉即觉悟",
    "灵流": "《文心雕龙·章句》'内义脉注' - 流即脉络",
    "灵运": "《庄子·天道》'天道运而无所积' - 运乃周行不殆",
    "灵踪": "李白《梦游天姥吟留别》'须行即骑访名山' - 踪即行迹",
    "灵愿": "《大学》'先治其国' - 愿乃心之所向",
    "灵览": "陆机《文赋》'伫中区以玄览' - 览即观照",
    "灵新": "《大学》'苟日新，日日新' - 新乃自新之功",
    "灵录": "《后汉书·应奉传》'时人谓之应录' - 录乃记录",
    "灵联": "《易·系辞上》'联缀其辞' - 联即连接",
    "灵讯": "《礼记·王制》'讯群臣' - 讯即询问",
    "灵任": "《论语·泰伯》'任重而道远' - 任乃肩负之事",
    "灵验": "《文心雕龙·知音》'验乎其言' - 验乃考校",
    "灵覆": "《易·系辞上》'曲成万物而不遗' - 覆即遍及",
    "灵书": "《文心雕龙·书记》'书者，舒也' - 书乃舒布其言",
    "灵脉": "《黄帝内经》'脉者，血之府也' - 脉为生命之征",
    "灵量": "《庄子·胠箧》'为之斗斛以量之' - 量乃度量衡",
    "灵警": "《荀子·王制》'警之以政' - 警即警示",
}


def resolve_tool_name(name: str) -> str:
    """
    解析工具名称，支持中文别名（雅正版）

    Args:
        name: 工具名称（英文或中文）

    Returns:
        标准的英文工具名
    """
    # 如果是中文，转换为英文
    if name in TOOL_ALIASES_CN_TO_EN:
        return TOOL_ALIASES_CN_TO_EN[name]

    # 如果已经是英文，直接返回
    return name


def get_tool_cn_name(english_name: str) -> Optional[str]:
    """
    获取工具的中文名（雅正版）

    Args:
        english_name: 英文工具名

    Returns:
        中文名，如果不存在返回 None
    """
    return TOOL_ALIASES_EN_TO_CN.get(english_name)


def get_tool_cn_description(name: str) -> str:
    """
    获取工具的中文描述（含国学释义）

    Args:
        name: 工具名称（英文或中文）

    Returns:
        中文描述
    """
    # 先解析为标准英文名
    en_name = resolve_tool_name(name)

    # 获取中文名
    cn_name = get_tool_cn_name(en_name)

    if cn_name:
        return TOOL_DESCRIPTIONS_CN.get(cn_name, f"{en_name}")

    return en_name


def get_tool_allusion(cn_name: str) -> Optional[str]:
    """
    获取工具的国学典故

    Args:
        cn_name: 中文名

    Returns:
        国学典故，如果不存在返回 None
    """
    return TOOL_ALLUSIONS.get(cn_name)


def list_all_tool_names() -> Dict[str, str]:
    """
    列出所有工具的中英文名映射（雅正版）

    Returns:
        {中文名: 英文名}
    """
    return TOOL_ALIASES_CN_TO_EN.copy()


# 示例使用
if __name__ == "__main__":
    print("=" * 70)
    print("LingFlow MCP Server - 灵系工具命名（雅正版）")
    print("众智混元，万法灵通")
    print("=" * 70)

    print("\n📋 所有工具列表:")
    print("-" * 70)
    for cn_name, en_name in TOOL_ALIASES_CN_TO_EN.items():
        desc = TOOL_DESCRIPTIONS_CN.get(cn_name, "")
        allusion = TOOL_ALLUSIONS.get(cn_name, "")
        print(f"\n  {en_name:30} → {cn_name:6}")
        print(f"    {desc}")
        if allusion:
            print(f"    🔖 {allusion}")

    print("\n" + "=" * 70)
    print("🔍 名称解析测试:")
    print("-" * 70)

    test_names = ["灵艺", "灵鉴", "灵新", "灵任", "list_skills"]
    for name in test_names:
        resolved = resolve_tool_name(name)
        desc = get_tool_cn_description(resolved)
        allusion = get_tool_allusion(name if name in TOOL_ALIASES_CN_TO_EN else get_tool_cn_name(resolved))
        print(f"\n  {name:10} → {resolved:20}")
        print(f"    {desc}")
        if allusion:
            print(f"    🔖 {allusion}")

    print("\n" + "=" * 70)
    print("修订统计:")
    print("-" * 70)
    print(f"  总工具数: {len(TOOL_ALIASES_CN_TO_EN)} 个")
    print(f"  双字名: {sum(1 for n in TOOL_ALIASES_CN_TO_EN if len(n) == 2)} 个")
    print(f"  三字名: {sum(1 for n in TOOL_ALIASES_CN_TO_EN if len(n) == 3)} 个")
    print(f"  含典故: {len(TOOL_ALLUSIONS)} 个")
    print("=" * 70)
