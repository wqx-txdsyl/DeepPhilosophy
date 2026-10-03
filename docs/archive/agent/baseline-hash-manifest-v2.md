# PHIAGENT Baseline Hash Manifest V2

> 最终 preservation commit（archive/phiagent-pre-orchestration-reset）的 authoritative baseline manifest。
> 取代 O0-R candidate（docs/PHIAGENT_BASELINE_HASH_MANIFEST_CANDIDATE.md，保留为 forensic artifact）。

## Scope 与口径

- 覆盖 preservation commit 全部 intended staged 文件：backend / frontend(app) / schools/data / docs / skills / scripts / 项目配置（AGENTS.md 等）—— 下表 81 项 + 本文件自身（V2 在 commit 中，但不进入自身 hash input，故不在下表）。
- 每项 sha256/size 取自 **staged blob**（`git cat-file blob :path`，实际入 commit 对象，非工作树假设值）。
- **BASELINE_MANIFEST_SHA256** = 对 80 个项目文件的 canonical bytes 取 SHA256（排除 V2 与 baseline report 两个自/互指流程产物——偏差已在 baseline report §5 文档化；report 本身逐文件哈希在下表第 81 行）。
- Canonical bytes: repo-relative POSIX path，UTF-8 lexical sort，每行 `<sha256><两个空格><relative_path>
`；canonical 行原文附于文末，可直接复算验证。

**BASELINE_MANIFEST_SHA256 = `e5605c4d8e5c8c6377cb75fdef28b1d4d0de701048a44183d4b0db54621070b1`**

## 逐文件清单（81 项）

| relative_path | tracked/untracked | size (bytes) | sha256 |
| --- | --- | --- | --- |
| `.agents/skills/add-author/SKILL.md` | untracked | 1847 | `f559ef134d45c35b7aedee6cb502605b4e0bb97e83f85b2f409a04b23a06ab80` |
| `.agents/skills/add-school/SKILL.md` | untracked | 963 | `18348977bebb53d07087031565bc0e0c43a1b91d1a8ece387d94ccef920ac4ea` |
| `.agents/skills/add-skill/SKILL.md` | untracked | 6401 | `ee609ae840d7e8d71b1e451f92e9fa9ce458a0904c9a96083bba664afba9f3e2` |
| `.agents/skills/add-subschool/SKILL.md` | untracked | 2741 | `edbee284ec95b8dc51d36ad29df288fcbfb4766c6916db35d22b015b9653b913` |
| `.agents/skills/agnes-image/SKILL.md` | untracked | 3699 | `f98cb23b4caa82a59873c000e8cf04d17d35222a2cb38d9ce9c766047b2cc9d4` |
| `.agents/skills/fetch-philosopher-img/SKILL.md` | untracked | 2585 | `eb09db317edb3ca62aa0ddaa2770ce8c8bb360b63c297d91e91f1b06de56dd1c` |
| `.agents/skills/fix-counts/SKILL.md` | untracked | 989 | `0dbb92f09e1d1a55b7530f9d3963d4285a6c2907f5ea053d08b7c8d424cfb001` |
| `.agents/skills/local-check/SKILL.md` | untracked | 1450 | `38d3ee6443f077736d35d568d4153f79c67b0b8950b4f9f433a6de9116f0b00b` |
| `.agents/skills/post-push/SKILL.md` | untracked | 1472 | `90e437daebc9c779760df0193678f93f28ce5ca126457e5d7768ba3bc3dd8569` |
| `.agents/skills/relationship-constellation/SKILL.md` | untracked | 4051 | `006d81f5372edd18a9a73f8bcf62235dbb5076f550b496c25caefeb6377d38cb` |
| `.agents/skills/school-bg-gen/SKILL.md` | untracked | 1147 | `a0f6c11b76dea07a876cf8e7216140e06ad4f92e66e6a0fc8834bfdf28209eff` |
| `.agents/skills/timeline-designer/SKILL.md` | untracked | 3374 | `c2a6d175ac44f45d9c7dfa8bbd632092167cf078e2957b7893fd5a457e0b5409` |
| `AGENTS.md` | untracked | 7872 | `f519fa86173f7e598135968f98652f64b8baab88a2b8629da91fcda132236571` |
| `app/public/schools/data/school_伊壁鸠鲁学派.json` | untracked | 27674 | `1ff1d405488c759178449fbb5f53323740ad0de1c67d04a8354e01e69f17b694` |
| `app/public/schools/data/school_分析哲学.json` | untracked | 25568 | `d45190647099bc30d2c535eb327b0bb8d578a4cde1d61054772cfe0174c7ca33` |
| `app/public/schools/data/school_前苏格拉底哲学.json` | untracked | 28895 | `dfea8d4ac45831a5f9fd7a193f53469b555e54eb166243f7aeaccc131bdbdba0` |
| `app/public/schools/data/school_怀疑论.json` | untracked | 32671 | `d4f2bac46b21ccc747c91a722b5a4ccd72829c8ed74b2d3c0e8a1a07f554f75a` |
| `app/public/schools/data/school_斯多葛学派.json` | untracked | 29920 | `a4d3d8c6b0a4a1927e3cedcddcfe383162b3b3daa5b56a6c83187e627504edeb` |
| `app/public/schools/data/school_新柏拉图主义.json` | untracked | 26745 | `826fce551c686b17bdb9fb52be36ebbb740e96b96506ed06dd9f3d4ca7bec085` |
| `app/public/schools/data/school_犬儒学派.json` | untracked | 30009 | `c7d41c1b36d726f82c5f9bf4cc457c1cbe728490049bf742451997ad7466dc23` |
| `app/src/App.css` | tracked | 32485 | `59220216b5fb909172ffd12a37a1392be59e6bc27e974501ed096248d12a7c55` |
| `app/src/components/ChapterReader.jsx` | tracked | 38390 | `16b6aca8236de0b984d6adc91edf274a3eb80c627f8df2e7e1a5261a4c931672` |
| `app/src/components/school/HeroSection.jsx` | tracked | 4086 | `ee6453b4d6fa7a65a35d28d2ca3dc6549f4eda59bd6ef1406b72affd16a64c91` |
| `app/src/pages/AuthorDetailPage.jsx` | tracked | 9880 | `016c13491d2d5f28ac435253ee3198cee83ba61b56403ee392372212a03241a1` |
| `app/src/pages/EasternPhilosophiesPage.jsx` | tracked | 8014 | `0d9c3ddbc7f95971c2c32e2254c31c389f114ca323148650d75f4ad0005a99af` |
| `app/src/pages/GenealogyPage.jsx` | tracked | 28630 | `97c7937204e319bab0e018283883be3bf2acbd8189ed9222fbbc598479bed8ee` |
| `app/src/pages/HomePage.css` | tracked | 10359 | `5b76025d1d4620e4ec60e51a56d68cf50ffb2811134eb99d320e4fc52d41e32f` |
| `app/src/pages/ProfilePage.jsx` | tracked | 24196 | `08af383fc3043b3e1f2d4482e95c3b209e434ae4b865acfbe79ead8561211a73` |
| `app/src/pages/ReaderPage.jsx` | tracked | 26712 | `37aad4c961a7ef5b308cb3041452cbb6b7bef5c1c01d30482afa31a3e063c03a` |
| `app/src/pages/SchoolDetailPage.jsx` | tracked | 34809 | `b61112fe1c6874ff8319e597d4eafb99f4b84593db1c4980a53705a253c1212d` |
| `app/src/pages/WesternPhilosophiesPage.jsx` | tracked | 9458 | `6254afbcc3c8dbda89cb6edd5399c42a14636977bde8a87d3782ac3eaa372068` |
| `app/src/pages/WorldPhilosophiesPage.jsx` | tracked | 14062 | `c2a2975f45416370c16ea2800a596aa8d19ba3cbada3d7717a35a2776e28127e` |
| `backend/agent_runtime.py` | tracked | 56521 | `5b649d81a44bd8be7d2369f1879e1b2e3540cf7caa234f1c0a4bb4eee858cb11` |
| `backend/answer_composer.py` | tracked | 31947 | `7dc028e4ce1d1a8b0563416a8c523366bbf6589fa921fab368a4e21395b25211` |
| `backend/engine_langgraph.py` | tracked | 151852 | `f642fc3282f434fd79871f7c07f07247d7233d87e1a157de748650046b2c8fc6` |
| `backend/epistemic_guard.py` | tracked | 58352 | `3a157fa0f72e8ddee5c529478c08dcd49e45f7aac8ae16de1170dc787d01e98f` |
| `backend/evidence_contract.py` | tracked | 35351 | `2c3bcccd6242c84b794d1175030984097b549c92f625e1e5c9f8c893216dd83d` |
| `backend/guard.py` | tracked | 9402 | `6d445566eddb8c0f9bf86a1583358849abf699d962306c6de832f69656c27df7` |
| `backend/interpretation_engine.py` | tracked | 33525 | `271806191766d1483f63c3c8522362b07112b06fa40d47eb35af666fd9b27764` |
| `backend/main.py` | tracked | 9271 | `9e1602f1180bcba5f3d0e02ba376a98e41c347ec3bf13f13be7eed8b13f81c9e` |
| `backend/philo_retrieval.py` | tracked | 16264 | `993ec8b110c0577217d3fd51f66a0d21c5311773f8ab83cc28c1272d6bbbd0d9` |
| `backend/quote_bound.py` | untracked | 23493 | `3c0b88c1e237c9a41e466742bfb4d2caee9581d73dae34793ac6b3faa2efca13` |
| `backend/reasoning_plan.py` | untracked | 54950 | `7c68b0ec67a83a0d5c2d22da1f7c307a2d29dae4e8d0e9e871e3ce389604e2a1` |
| `backend/routes/agent.py` | tracked | 15415 | `74796464122a86f33f189ea4afdf9424a58d7fcc609981bf83de474c85d4d249` |
| `backend/routes/agent_core.py` | tracked | 16832 | `408699acbaf8e739d6f66acc06d79c0f3f05be1af964ee779587fc1d59fad1e7` |
| `backend/routes/agent_tools_eval.py` | tracked | 56292 | `bc38592b693e3c3de80e493264d6d1eb58f0f9e1b4da80b340fa96bb9591c0d4` |
| `backend/routes/agent_tools_memory.py` | tracked | 40034 | `757dffaf617b4de1691bc9d5784f7d84fe4f5259f9e3c84d9143146abe4331c7` |
| `backend/routes/agent_tools_retrieval.py` | tracked | 28714 | `17a5f7ca8f767f2e172c59b288cc7529d88322ffd4b3d44e8e7e685ed6920753` |
| `backend/routes/auth_routes.py` | tracked | 1126 | `766df1b3228ae224254594865b2bf4e338aec72b8b33540a57528afb76d091fc` |
| `backend/routes/upload.py` | tracked | 5582 | `16dc5220ab198835a6c4dc4898f55910e09bfe7127608a7bdfc840a534f2140e` |
| `backend/semantic_obligations.py` | tracked | 11935 | `746db97f17390a104ec97c792f89479ed9764d5db283ab1a575914be1db057df` |
| `backend/tests/test_answer_composer.py` | tracked | 18697 | `d3d112343c7f2fccb34c841b01c6a5f4cbc1fe1ddc49391e1885d42228d43f64` |
| `backend/tests/test_interpretation_engine.py` | tracked | 18509 | `2760d921384db6f7d4efcd5b5ec5b3b6b30d64f3f66ad6dbc99baf79f8fbfa10` |
| `backend/tests/test_patch1.py` | untracked | 15375 | `4f81a8198f948bf43c9e67a2979977e59cf46e7b6edc96fbd3e456bdabfc69a8` |
| `backend/tests/test_patch1_1.py` | untracked | 27240 | `c36f2bb67d1a998456856dc5fb0cd717d72750394288fe156092fc99bedb8ae9` |
| `backend/tests/test_phase_s.py` | tracked | 42046 | `69ccb143e6522ace78b9d061355fd94ad22d85165b862ba78e62c77e19cfd52a` |
| `backend/tests/test_phase_t.py` | untracked | 38232 | `9d98b490b76c632a91a71a4337d3c7f56e68c39da21e8da85633685372df2d80` |
| `backend/tests/test_phase_t1.py` | untracked | 16704 | `7c15cd8cd8b9d444a91dfc09c55c126309c8973bf60a18777cc2914993ce1140` |
| `backend/tests/test_security.py` | tracked | 5884 | `032f59540875db66388a4b54a95d983cf618d7e5e7b7448ec2d543eb19268d8b` |
| `backend/tool_contracts.py` | untracked | 38982 | `4136e24e2ca2e7a92dea8d02e3ed0ead58a1c7d4db64e286942ab3e4c7996024` |
| `docs/BOOK_SHELL_INVENTORY.md` | untracked | 9875 | `20b76ab59a4eaac0878ff696a00e5f29c0434b6aad761416dcfbaa4b0ab7114f` |
| `docs/PHIAGENT_BACKEND_DECISION_AUTHORITY_MAP.md` | untracked | 19544 | `2e378447e91b087978310e1ec25c1d224953787088365e1203e38ece5c932e25` |
| `docs/PHIAGENT_BACKEND_DIAGNOSTIC.md` | untracked | 250708 | `769a9cfbd55cb9ba4fe4c8ab3caa1634f855196c3c9dabb3fee6cbfe32da413e` |
| `docs/PHIAGENT_BACKEND_FULL_ARCHITECTURE_AUDIT.md` | untracked | 58389 | `20544c59b505492af46eb2b53e2a02d2702547a428d730732e5aef7564fe2cb1` |
| `docs/PHIAGENT_BACKEND_PATCH1_1_REGRESSION.md` | untracked | 44190 | `b2ac8836172498caeb53325e9a7209cd629494d166e59c5d8cb116653628885c` |
| `docs/PHIAGENT_BACKEND_PATCH1_FINAL_GATE.md` | untracked | 113658 | `49051ef098010117763678fe861c24d813bae7a91626fec7eeeddbbb57fe8560` |
| `docs/PHIAGENT_BACKEND_PATCH1_REGRESSION.md` | untracked | 48422 | `b2108b133ca1e0862425a7b09c387d076948ef786d3c50b35823d0864800e924` |
| `docs/PHIAGENT_BACKEND_QUALITY_GATE2.md` | untracked | 194454 | `9d472e69f6c9d26ee7a0ab79ae230708757dcf2b61166df8647d9bba2abcc4f9` |
| `docs/PHIAGENT_BASELINE_HASH_MANIFEST_CANDIDATE.md` | untracked | 34664 | `d236e124c23cec63b26561a874d739db3412d83a4c774ca68d6c860d4d1bc1fe` |
| `docs/PHIAGENT_O0_BASELINE_RECONCILIATION.md` | untracked | 17575 | `091b420ad6c7bfb53f2d29b7d1e20e28bb2fa08ad064f8e949056d5becac998a` |
| `docs/PHIAGENT_ORCHESTRATION_RESET_BASELINE.md` | untracked | 12046 | `80196af7d0fad4728ab37789d59ba37c5b551cee9fcf112da7fc13dfce4ac33b` |
| `docs/PHIAGENT_PHASE_T1_SOURCE_VERIFICATION_REGRESSION.md` | untracked | 17830 | `81dbaef6fc72ac87d0663e4b0f010f1df8ad44f601a921f0cb2fb022c46e4d25` |
| `docs/PHIAGENT_PHASE_T_REGRESSION.md` | untracked | 14197 | `ba989e5d1be9737b23a8cad5de42a7f64e31d6406ebe904f687d18a0812bba21` |
| `docs/PHIAGENT_PHASE_T_TOOL_ARCHITECTURE.md` | untracked | 8776 | `288e42cde0ebdbcdc2d0fbccad89d7332b9d1fe08ec704877f285f64efcfb9ce` |
| `docs/PHIAGENT_TOOL_ARCHITECTURE.md` | untracked | 10790 | `1098c337678bd12de7af96213d5768278a779e1a956abbf3b869d33f2be1b761` |
| `docs/PhiAgent_Conversation_Workspace_Design_Spec_v1.0.md` | untracked | 21100 | `47e0b4c2b34f2418c892ceb6d4455440a767ec593990d486a3b4d03ab8bbab1c` |
| `docs/PhiAgent_Conversation_Workspace_Refactor.md` | untracked | 13790 | `49710e4f29c73f47e9a61962fae5d376d11ace7fb75e1b3added3faad09618a9` |
| `docs/PhiAgent_agent_deploy.md` | untracked | 6312 | `e0213383eb8b0f3025a9c607a3cbf41fdc2d3ea7043d94b922a7318efc455017` |
| `docs/分章标准规范.md` | untracked | 7223 | `58a6964e3f331df6c0ee55bd81cf1a037b7bfc13ff777051cd084c41580b7a93` |
| `docs/设计说明-20260818-UI优化.md` | untracked | 15345 | `9bed228c984ec78c493826dbb6a61847c4259b077ff07d39fde5f84d4ce1a289` |
| `scripts/build_phiagent_static.py` | untracked | 1668 | `d80759ff7c4bf6491d7574447f7812c2a9dba451b40cfc184d3015c9f6f6436e` |

## Canonical 行原文（= 聚合 hash 输入，80 行）

```
f559ef134d45c35b7aedee6cb502605b4e0bb97e83f85b2f409a04b23a06ab80  .agents/skills/add-author/SKILL.md
18348977bebb53d07087031565bc0e0c43a1b91d1a8ece387d94ccef920ac4ea  .agents/skills/add-school/SKILL.md
ee609ae840d7e8d71b1e451f92e9fa9ce458a0904c9a96083bba664afba9f3e2  .agents/skills/add-skill/SKILL.md
edbee284ec95b8dc51d36ad29df288fcbfb4766c6916db35d22b015b9653b913  .agents/skills/add-subschool/SKILL.md
f98cb23b4caa82a59873c000e8cf04d17d35222a2cb38d9ce9c766047b2cc9d4  .agents/skills/agnes-image/SKILL.md
eb09db317edb3ca62aa0ddaa2770ce8c8bb360b63c297d91e91f1b06de56dd1c  .agents/skills/fetch-philosopher-img/SKILL.md
0dbb92f09e1d1a55b7530f9d3963d4285a6c2907f5ea053d08b7c8d424cfb001  .agents/skills/fix-counts/SKILL.md
38d3ee6443f077736d35d568d4153f79c67b0b8950b4f9f433a6de9116f0b00b  .agents/skills/local-check/SKILL.md
90e437daebc9c779760df0193678f93f28ce5ca126457e5d7768ba3bc3dd8569  .agents/skills/post-push/SKILL.md
006d81f5372edd18a9a73f8bcf62235dbb5076f550b496c25caefeb6377d38cb  .agents/skills/relationship-constellation/SKILL.md
a0f6c11b76dea07a876cf8e7216140e06ad4f92e66e6a0fc8834bfdf28209eff  .agents/skills/school-bg-gen/SKILL.md
c2a6d175ac44f45d9c7dfa8bbd632092167cf078e2957b7893fd5a457e0b5409  .agents/skills/timeline-designer/SKILL.md
f519fa86173f7e598135968f98652f64b8baab88a2b8629da91fcda132236571  AGENTS.md
1ff1d405488c759178449fbb5f53323740ad0de1c67d04a8354e01e69f17b694  app/public/schools/data/school_伊壁鸠鲁学派.json
d45190647099bc30d2c535eb327b0bb8d578a4cde1d61054772cfe0174c7ca33  app/public/schools/data/school_分析哲学.json
dfea8d4ac45831a5f9fd7a193f53469b555e54eb166243f7aeaccc131bdbdba0  app/public/schools/data/school_前苏格拉底哲学.json
d4f2bac46b21ccc747c91a722b5a4ccd72829c8ed74b2d3c0e8a1a07f554f75a  app/public/schools/data/school_怀疑论.json
a4d3d8c6b0a4a1927e3cedcddcfe383162b3b3daa5b56a6c83187e627504edeb  app/public/schools/data/school_斯多葛学派.json
826fce551c686b17bdb9fb52be36ebbb740e96b96506ed06dd9f3d4ca7bec085  app/public/schools/data/school_新柏拉图主义.json
c7d41c1b36d726f82c5f9bf4cc457c1cbe728490049bf742451997ad7466dc23  app/public/schools/data/school_犬儒学派.json
59220216b5fb909172ffd12a37a1392be59e6bc27e974501ed096248d12a7c55  app/src/App.css
16b6aca8236de0b984d6adc91edf274a3eb80c627f8df2e7e1a5261a4c931672  app/src/components/ChapterReader.jsx
ee6453b4d6fa7a65a35d28d2ca3dc6549f4eda59bd6ef1406b72affd16a64c91  app/src/components/school/HeroSection.jsx
016c13491d2d5f28ac435253ee3198cee83ba61b56403ee392372212a03241a1  app/src/pages/AuthorDetailPage.jsx
0d9c3ddbc7f95971c2c32e2254c31c389f114ca323148650d75f4ad0005a99af  app/src/pages/EasternPhilosophiesPage.jsx
97c7937204e319bab0e018283883be3bf2acbd8189ed9222fbbc598479bed8ee  app/src/pages/GenealogyPage.jsx
5b76025d1d4620e4ec60e51a56d68cf50ffb2811134eb99d320e4fc52d41e32f  app/src/pages/HomePage.css
08af383fc3043b3e1f2d4482e95c3b209e434ae4b865acfbe79ead8561211a73  app/src/pages/ProfilePage.jsx
37aad4c961a7ef5b308cb3041452cbb6b7bef5c1c01d30482afa31a3e063c03a  app/src/pages/ReaderPage.jsx
b61112fe1c6874ff8319e597d4eafb99f4b84593db1c4980a53705a253c1212d  app/src/pages/SchoolDetailPage.jsx
6254afbcc3c8dbda89cb6edd5399c42a14636977bde8a87d3782ac3eaa372068  app/src/pages/WesternPhilosophiesPage.jsx
c2a2975f45416370c16ea2800a596aa8d19ba3cbada3d7717a35a2776e28127e  app/src/pages/WorldPhilosophiesPage.jsx
5b649d81a44bd8be7d2369f1879e1b2e3540cf7caa234f1c0a4bb4eee858cb11  backend/agent_runtime.py
7dc028e4ce1d1a8b0563416a8c523366bbf6589fa921fab368a4e21395b25211  backend/answer_composer.py
f642fc3282f434fd79871f7c07f07247d7233d87e1a157de748650046b2c8fc6  backend/engine_langgraph.py
3a157fa0f72e8ddee5c529478c08dcd49e45f7aac8ae16de1170dc787d01e98f  backend/epistemic_guard.py
2c3bcccd6242c84b794d1175030984097b549c92f625e1e5c9f8c893216dd83d  backend/evidence_contract.py
6d445566eddb8c0f9bf86a1583358849abf699d962306c6de832f69656c27df7  backend/guard.py
271806191766d1483f63c3c8522362b07112b06fa40d47eb35af666fd9b27764  backend/interpretation_engine.py
9e1602f1180bcba5f3d0e02ba376a98e41c347ec3bf13f13be7eed8b13f81c9e  backend/main.py
993ec8b110c0577217d3fd51f66a0d21c5311773f8ab83cc28c1272d6bbbd0d9  backend/philo_retrieval.py
3c0b88c1e237c9a41e466742bfb4d2caee9581d73dae34793ac6b3faa2efca13  backend/quote_bound.py
7c68b0ec67a83a0d5c2d22da1f7c307a2d29dae4e8d0e9e871e3ce389604e2a1  backend/reasoning_plan.py
74796464122a86f33f189ea4afdf9424a58d7fcc609981bf83de474c85d4d249  backend/routes/agent.py
408699acbaf8e739d6f66acc06d79c0f3f05be1af964ee779587fc1d59fad1e7  backend/routes/agent_core.py
bc38592b693e3c3de80e493264d6d1eb58f0f9e1b4da80b340fa96bb9591c0d4  backend/routes/agent_tools_eval.py
757dffaf617b4de1691bc9d5784f7d84fe4f5259f9e3c84d9143146abe4331c7  backend/routes/agent_tools_memory.py
17a5f7ca8f767f2e172c59b288cc7529d88322ffd4b3d44e8e7e685ed6920753  backend/routes/agent_tools_retrieval.py
766df1b3228ae224254594865b2bf4e338aec72b8b33540a57528afb76d091fc  backend/routes/auth_routes.py
16dc5220ab198835a6c4dc4898f55910e09bfe7127608a7bdfc840a534f2140e  backend/routes/upload.py
746db97f17390a104ec97c792f89479ed9764d5db283ab1a575914be1db057df  backend/semantic_obligations.py
d3d112343c7f2fccb34c841b01c6a5f4cbc1fe1ddc49391e1885d42228d43f64  backend/tests/test_answer_composer.py
2760d921384db6f7d4efcd5b5ec5b3b6b30d64f3f66ad6dbc99baf79f8fbfa10  backend/tests/test_interpretation_engine.py
4f81a8198f948bf43c9e67a2979977e59cf46e7b6edc96fbd3e456bdabfc69a8  backend/tests/test_patch1.py
c36f2bb67d1a998456856dc5fb0cd717d72750394288fe156092fc99bedb8ae9  backend/tests/test_patch1_1.py
69ccb143e6522ace78b9d061355fd94ad22d85165b862ba78e62c77e19cfd52a  backend/tests/test_phase_s.py
9d98b490b76c632a91a71a4337d3c7f56e68c39da21e8da85633685372df2d80  backend/tests/test_phase_t.py
7c15cd8cd8b9d444a91dfc09c55c126309c8973bf60a18777cc2914993ce1140  backend/tests/test_phase_t1.py
032f59540875db66388a4b54a95d983cf618d7e5e7b7448ec2d543eb19268d8b  backend/tests/test_security.py
4136e24e2ca2e7a92dea8d02e3ed0ead58a1c7d4db64e286942ab3e4c7996024  backend/tool_contracts.py
20b76ab59a4eaac0878ff696a00e5f29c0434b6aad761416dcfbaa4b0ab7114f  docs/BOOK_SHELL_INVENTORY.md
2e378447e91b087978310e1ec25c1d224953787088365e1203e38ece5c932e25  docs/PHIAGENT_BACKEND_DECISION_AUTHORITY_MAP.md
769a9cfbd55cb9ba4fe4c8ab3caa1634f855196c3c9dabb3fee6cbfe32da413e  docs/PHIAGENT_BACKEND_DIAGNOSTIC.md
20544c59b505492af46eb2b53e2a02d2702547a428d730732e5aef7564fe2cb1  docs/PHIAGENT_BACKEND_FULL_ARCHITECTURE_AUDIT.md
b2ac8836172498caeb53325e9a7209cd629494d166e59c5d8cb116653628885c  docs/PHIAGENT_BACKEND_PATCH1_1_REGRESSION.md
49051ef098010117763678fe861c24d813bae7a91626fec7eeeddbbb57fe8560  docs/PHIAGENT_BACKEND_PATCH1_FINAL_GATE.md
b2108b133ca1e0862425a7b09c387d076948ef786d3c50b35823d0864800e924  docs/PHIAGENT_BACKEND_PATCH1_REGRESSION.md
9d472e69f6c9d26ee7a0ab79ae230708757dcf2b61166df8647d9bba2abcc4f9  docs/PHIAGENT_BACKEND_QUALITY_GATE2.md
d236e124c23cec63b26561a874d739db3412d83a4c774ca68d6c860d4d1bc1fe  docs/PHIAGENT_BASELINE_HASH_MANIFEST_CANDIDATE.md
091b420ad6c7bfb53f2d29b7d1e20e28bb2fa08ad064f8e949056d5becac998a  docs/PHIAGENT_O0_BASELINE_RECONCILIATION.md
81dbaef6fc72ac87d0663e4b0f010f1df8ad44f601a921f0cb2fb022c46e4d25  docs/PHIAGENT_PHASE_T1_SOURCE_VERIFICATION_REGRESSION.md
ba989e5d1be9737b23a8cad5de42a7f64e31d6406ebe904f687d18a0812bba21  docs/PHIAGENT_PHASE_T_REGRESSION.md
288e42cde0ebdbcdc2d0fbccad89d7332b9d1fe08ec704877f285f64efcfb9ce  docs/PHIAGENT_PHASE_T_TOOL_ARCHITECTURE.md
1098c337678bd12de7af96213d5768278a779e1a956abbf3b869d33f2be1b761  docs/PHIAGENT_TOOL_ARCHITECTURE.md
47e0b4c2b34f2418c892ceb6d4455440a767ec593990d486a3b4d03ab8bbab1c  docs/PhiAgent_Conversation_Workspace_Design_Spec_v1.0.md
49710e4f29c73f47e9a61962fae5d376d11ace7fb75e1b3added3faad09618a9  docs/PhiAgent_Conversation_Workspace_Refactor.md
e0213383eb8b0f3025a9c607a3cbf41fdc2d3ea7043d94b922a7318efc455017  docs/PhiAgent_agent_deploy.md
58a6964e3f331df6c0ee55bd81cf1a037b7bfc13ff777051cd084c41580b7a93  docs/分章标准规范.md
9bed228c984ec78c493826dbb6a61847c4259b077ff07d39fde5f84d4ce1a289  docs/设计说明-20260818-UI优化.md
d80759ff7c4bf6491d7574447f7812c2a9dba451b40cfc184d3015c9f6f6436e  scripts/build_phiagent_static.py
```

复算: `sha256(上述 80 行 bytes) = e5605c4d8e5c8c6377cb75fdef28b1d4d0de701048a44183d4b0db54621070b1`
