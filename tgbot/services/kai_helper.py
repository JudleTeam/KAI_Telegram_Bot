from kai_parser import KaiParser


async def add_group_schedule(group_name: int):
    k = KaiParser()
    group_id = await k.get_group_id(group_name)
    response = await k.get_group_schedule(group_id)
    if response:
