import asyncio
import time

async def main():
    from cairio import client as ca
    ca.autoConfig(collection='spikeforest',key='spikeforest2-readwrite',ask_password=True)
    count=30
    test_str='b*xxxxxxxxxxxxxx'

    timer=time.time()
    for num in range(count):
        ca.saveObject(key=dict(num=num),object=dict(testing=test_str*num))
    elapsed_sec=time.time()-timer
    print('Elapsed: {}'.format(elapsed_sec))

    timer=time.time()
    tasks=[]
    for num in range(count):
        tasks.append(ca.saveObjectAsync(key=dict(num=num),object=dict(testing=test_str*num)))
    await asyncio.gather(*tasks)
    elapsed_sec=time.time()-timer
    print('Elapsed: {}'.format(elapsed_sec))

asyncio.get_event_loop().run_until_complete(main())