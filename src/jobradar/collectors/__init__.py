from . import consider, feeds, getro, jobstash, mycareersfuture, rebase, telegram, web3career

AGGREGATORS = {
    "jobstash": jobstash.collect,
    "getro": getro.collect,
    "consider": consider.collect,
    "web3career": web3career.collect,
    "cryptojobslist": feeds.cryptojobslist,
    "cryptocurrencyjobs": feeds.cryptocurrencyjobs,
    "web3vacancy": feeds.web3vacancy,
    "cryptojobs": feeds.cryptojobs,
    "eleduck": feeds.eleduck,
    "rebase": rebase.collect,
    "telegram": telegram.collect,
    "mycareersfuture": mycareersfuture.collect,
}
