from linkhandlers.tiktoklink import TiktokLink
from tests.rewrite.cases import Case, Seed

HANDLER = TiktokLink

CASES = [
    Case("video", "https://www.tiktok.com/@user/video/7000000000000000000",
         ["https://kktiktok.com/@user/video/7000000000000000000"]),
    Case("query-kept", "https://www.tiktok.com/@user/video/7000000000000000000?is_from_webapp=1&sender_device=pc",
         ["https://kktiktok.com/@user/video/7000000000000000000?is_from_webapp=1&sender_device=pc"]),
    Case("photo", "https://www.tiktok.com/@user/photo/7000000000000000000",
         ["https://kktiktok.com/@user/photo/7000000000000000000"]),
    Case("vt-short", "https://vt.tiktok.com/ZSabc123/", ["https://vt.kktiktok.com/ZSabc123/"]),
    Case("already-fixed", "https://kktiktok.com/@user/video/7000000000000000000"),
    Case("candidate-provider-ignored", "https://tnktok.com/@user/video/7000000000000000000"),
    Case("vm-short", "https://vm.tiktok.com/ZMabc123/", ["https://vm.kktiktok.com/ZMabc123/"],
         bug="vm.tiktok.com short links are not fixed (#9)"),
    Case("no-www", "https://tiktok.com/@user/video/7000000000000000000",
         ["https://kktiktok.com/@user/video/7000000000000000000"],
         bug="tiktok.com links without www. are not fixed (#9)"),
]

SEEDS = [
    Seed("https://www.tiktok.com/@user/video/7000000000000000001", "7000000000000000001"),
    Seed("https://vt.tiktok.com/ZSabc123/", "ZSabc123"),
]
