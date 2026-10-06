# PHIAGENT_BASELINE_HASH_MANIFEST_CANDIDATE

- 性质: 只读基线清单（O0-R 产物）。生成时刻: 2026-09-04（O0 Baseline Reconciliation Gate 执行时）。
- 基线 HEAD: `ec09e04da914d55ba3904fc5812785b2f81729f6`（master）。
- 条目数: 141（tracked=123, untracked=18）。
- 本清单取代 AUDIT-01 的聚合 digest `716d7175ac9901ae3f57e74fcb28205739f84b0bda194606142da4c68dc000a8`：
  该 digest 只记录了「对全部 backend 文件逐一 sha256sum 后再聚合」，未写死聚合算法/文件清单/顺序，
  不可复现。今后 O0 只认本清单口径：**逐文件 sha256 + 规范化 MANIFEST_SHA256**。

## 1. 范围（SCOPE）

- `backend/**/*.py`（全部 Python 生产源码 + 测试 + 工具；含 untracked 的运行时新模块）
- `docs/PHIAGENT_*.md`（AUDIT-01 / T1 / PATCH1 / QUALITY_GATE2 等 PhiAgent 审计-回归文档系列，共 11 份）

## 2. 明确排除（EXCLUSIONS）

- `.env` 及任何 secret、密钥材料
- `__pycache__/`、`*.pyc`、`.pytest_cache/`
- `backend/data/` 运行时数据（jsonl trace / stats / embeddings / agent_memory；其中唯一 `.py` 文件
  `backend/data/__init__.py` 为 git 跟踪的空包标记，属源码，**已包含**在清单内）
- 临时 json、`backend/tools/_tmp/` 类临时脚本（当前不存在）
- 本 Gate 的两份输出文档（生成于哈希之后，按名排除）：
  - `docs/PHIAGENT_BASELINE_HASH_MANIFEST_CANDIDATE.md`（本文档）
  - `docs/PHIAGENT_O0_BASELINE_RECONCILIATION.md`
  后续 O0 阶段若需冻结它们，应生成新版本清单（v2）。

## 3. 规范算法（写死，不可变更）

1. path 使用 repo-relative POSIX path（`/` 分隔，不含 `F:` 盘符）
2. UTF-8 lexical sort by path（码点序，等价 UTF-8 字节序）
3. 每行: `<sha256><两个空格><relative_path>
`（sha256 为小写 hex，64 字符）
4. 对完整 manifest bytes（全部行顺序拼接，含每行结尾 `
`）再取 sha256 → `MANIFEST_SHA256`

## 4. 逐文件清单

| relative_path | tracked | size (bytes) | sha256 |
|---|---|---|---|
| `backend/__init__.py` | tracked | 25 | `5f041a917482899433ab5eedcdd3e03d2edf8091886828fc418217f56bcd8075` |
| `backend/admin.py` | tracked | 8044 | `b7d2868992bd84cffb57ad2be1d97e10a0e080a332feb59319613ee6fdca7559` |
| `backend/agent_runtime.py` | tracked | 57482 | `01f173f156102f1aa643f1e99ebcb9a37aa2d3b21900892e3bd8a56a85019470` |
| `backend/agents.py` | tracked | 25166 | `0c4c18aa5b914a3eac94e4de3f9b8e3dc507ec60652fd49324f4480afdc8f580` |
| `backend/answer_composer.py` | tracked | 31947 | `7dc028e4ce1d1a8b0563416a8c523366bbf6589fa921fab368a4e21395b25211` |
| `backend/auth.py` | tracked | 31005 | `a1165a72c4be2b1991d29d1a9ac97cb85052912f65278bed2b987a09018d745a` |
| `backend/auth_deps.py` | tracked | 1370 | `bc76bd7356a2d96c1df015931972caf26c6e0d80790ed0ff82df67770009feae` |
| `backend/config.py` | tracked | 5013 | `9a4994514b96feefebafa8be3c3b55230b698a6ecc1749a4937f9e06db1b55d4` |
| `backend/data/__init__.py` | tracked | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `backend/db.py` | tracked | 2243 | `6ffba7224e0ff922e9c9e25ce4268b0cfbaadb89fd78dbc9b1ebf83803bebb8e` |
| `backend/drawio_convert.py` | tracked | 4977 | `1b112c6b99bbe0210a5f04778fabfdb91f81121d385e5e76d3e078c378695a62` |
| `backend/engine_langgraph.py` | tracked | 151852 | `f642fc3282f434fd79871f7c07f07247d7233d87e1a157de748650046b2c8fc6` |
| `backend/epistemic_guard.py` | tracked | 58352 | `3a157fa0f72e8ddee5c529478c08dcd49e45f7aac8ae16de1170dc787d01e98f` |
| `backend/eval_agent.py` | tracked | 5011 | `e77763f957a631440df2f4ea9e8c85629bdf6d8cb2f1e8915bf706fb96a36ce0` |
| `backend/evaluation_suite.py` | tracked | 16886 | `3bebbb87e9a284f3275b8c77922d4771b59036a4c84c29987582c22df1bab063` |
| `backend/evidence_contract.py` | tracked | 35351 | `2c3bcccd6242c84b794d1175030984097b549c92f625e1e5c9f8c893216dd83d` |
| `backend/fix_bios.py` | tracked | 2418 | `570e0eb7f37c96ccb813ebcabcacd8833c97ae082ff60f33157911fa4347f66b` |
| `backend/guard.py` | tracked | 9402 | `6d445566eddb8c0f9bf86a1583358849abf699d962306c6de832f69656c27df7` |
| `backend/interpretation_engine.py` | tracked | 33525 | `271806191766d1483f63c3c8522362b07112b06fa40d47eb35af666fd9b27764` |
| `backend/main.py` | tracked | 9271 | `9e1602f1180bcba5f3d0e02ba376a98e41c347ec3bf13f13be7eed8b13f81c9e` |
| `backend/mcp_client.py` | tracked | 4216 | `91d8b9f3846744591fbe6ad28ce7532b8e5bbbaaa1f1c765b463649e0fab984f` |
| `backend/mcp_servers/demo_server.py` | tracked | 655 | `35d34c95f4efbddc994d3525d505a3807dbec7f8638dceddd87aefa7b0c649dc` |
| `backend/mcp_servers/phiagent.py` | tracked | 3138 | `5d260061515d0a7eb018e873e304fd07e6642ba442f91d5b911fc4232fcde546` |
| `backend/models/__init__.py` | tracked | 1317 | `42e2b7af7e1902be3b3ea07ed03812928c92adf14e5da8d76435f6315c9b877a` |
| `backend/modules/__init__.py` | tracked | 48 | `f3a1aad10a0154f4b64bc38ad90338ccbc3680bc3fa011555d4a426a74e2ff4a` |
| `backend/modules/document_loader.py` | tracked | 11006 | `fb684ac51f8f4c6e3d0d365a1e617eba01ed8af9d0ce7d0374c750c1b5dbb72f` |
| `backend/modules/embedding.py` | tracked | 5974 | `2dce8f6797cb9955b3ba2ef1761f7855e77c1c3e0de5ca755e18d8d553ca9ee7` |
| `backend/modules/llm_client.py` | tracked | 3090 | `b4af81d670e2bcdf6506275a7b569a320ed4d5c2bdcc3209febe7f6a255edd7f` |
| `backend/modules/ocr_engine.py` | tracked | 3880 | `4df1ab5e491e0282a82cd5b94f4b714d9fdd379f68dd7d97fc83c1d4de56936a` |
| `backend/modules/rag_chain.py` | tracked | 4636 | `21fc73113675ff1c1034b3f8bb16baa66f617ec99500bb4b80f2cc60dcbebbf4` |
| `backend/modules/text_processor.py` | tracked | 6341 | `fc34935bd5a1b58d02b4fbd2823969083af9a03365d01f4d28b62456ed571a91` |
| `backend/modules/vector_store.py` | tracked | 6849 | `f6e74acfeea75564ef86c2b40453e29a83d784aff4d7501dcbbc747d64fdca79` |
| `backend/philo_retrieval.py` | tracked | 16264 | `993ec8b110c0577217d3fd51f66a0d21c5311773f8ab83cc28c1272d6bbbd0d9` |
| `backend/quote_bound.py` | untracked | 23493 | `3c0b88c1e237c9a41e466742bfb4d2caee9581d73dae34793ac6b3faa2efca13` |
| `backend/reasoning_plan.py` | untracked | 54950 | `7c68b0ec67a83a0d5c2d22da1f7c307a2d29dae4e8d0e9e871e3ce389604e2a1` |
| `backend/routes/__init__.py` | tracked | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `backend/routes/account.py` | tracked | 1243 | `19c3337f2530e3b204a403595768ed2fe475b37ae775ebf4dcfe02c11639919d` |
| `backend/routes/admin_routes.py` | tracked | 642 | `661a8393e7c7e568203b56fe41f7e38bb5631ef7e6daf2fc1b24a0fe01075a5d` |
| `backend/routes/agent.py` | tracked | 15415 | `74796464122a86f33f189ea4afdf9424a58d7fcc609981bf83de474c85d4d249` |
| `backend/routes/agent_core.py` | tracked | 16832 | `408699acbaf8e739d6f66acc06d79c0f3f05be1af964ee779587fc1d59fad1e7` |
| `backend/routes/agent_llm.py` | tracked | 5612 | `7529d1893c822d16e66d3087e07b2f2e4eeab3e2da9bc64ae62043e27604e086` |
| `backend/routes/agent_sse.py` | tracked | 3291 | `9c29adc78d36ae3da1e9622a95e97ab2fff7a65ae951499914da93b4b76d4fa7` |
| `backend/routes/agent_tools_eval.py` | tracked | 56292 | `bc38592b693e3c3de80e493264d6d1eb58f0f9e1b4da80b340fa96bb9591c0d4` |
| `backend/routes/agent_tools_memory.py` | tracked | 40034 | `757dffaf617b4de1691bc9d5784f7d84fe4f5259f9e3c84d9143146abe4331c7` |
| `backend/routes/agent_tools_retrieval.py` | tracked | 28714 | `17a5f7ca8f767f2e172c59b288cc7529d88322ffd4b3d44e8e7e685ed6920753` |
| `backend/routes/ai.py` | tracked | 7873 | `2e71b51a4aaf1ad462bdb787082251e1c6ce2b28bf6c3093e542bb3d63ef0b6e` |
| `backend/routes/auth_routes.py` | tracked | 1126 | `766df1b3228ae224254594865b2bf4e338aec72b8b33540a57528afb76d091fc` |
| `backend/routes/authors.py` | tracked | 12314 | `76ba7495e214bcb51f66ec9348903824f6b137f6129b8041ebf3861108996183` |
| `backend/routes/books.py` | tracked | 9996 | `d5c8703f081a73b7085c240bba10bf517a32f8d856f513be4dd05a85415eb226` |
| `backend/routes/health.py` | tracked | 1787 | `706375f3f2dcf082418607e521a6b34a91c1d66ce85fa78201c3787c694ff8b9` |
| `backend/routes/history.py` | tracked | 2811 | `58ef9dae88654571099dc411571a3ce6343e1aa44f9000cb9d60610c5baf29e5` |
| `backend/routes/knowledge.py` | tracked | 4179 | `ef2c156efee42ccf589b7a0d41aef10a7499507e42509065a42aa88783ff0492` |
| `backend/routes/openai_compat.py` | tracked | 6521 | `a21dbe9c72f0cedaac176afcccf9f7fa5bcd6a074dd0c2e559eb8af3629c024a` |
| `backend/routes/sync.py` | tracked | 2492 | `59facba450aab1ef2cc5704d2b48fd807145eeb0c9e39dc890788bc7e168f1ce` |
| `backend/routes/text.py` | tracked | 7229 | `2e5674aa641fec078f03cdeff5d01aed4f5726d3a68175065b8ee3f39fedce4d` |
| `backend/routes/upload.py` | tracked | 5582 | `16dc5220ab198835a6c4dc4898f55910e09bfe7127608a7bdfc840a534f2140e` |
| `backend/routes/user.py` | tracked | 2578 | `3fa554db9ae3746df45a544120769e756ace380142525336da61120ddcec355a` |
| `backend/semantic_obligations.py` | tracked | 11935 | `746db97f17390a104ec97c792f89479ed9764d5db283ab1a575914be1db057df` |
| `backend/services/__init__.py` | tracked | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `backend/services/book_scanner.py` | tracked | 17273 | `4b640c20b223f182ee9fc1f1ed416e79059f009d43086761ab94da6da3a117d8` |
| `backend/services/summaries.py` | tracked | 4644 | `fe1d69710883ae5423aae76b8e5910d2efef630855d39d4a8ccc12e45e0a535e` |
| `backend/services/tag_utils.py` | tracked | 5013 | `a72fd3687d4ee420e7ee450744be452f409b3969f893e8a9b99c730de0fecbd1` |
| `backend/tests/__init__.py` | tracked | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `backend/tests/regression_oldman_sea.py` | tracked | 17257 | `85f3413e2baf7bd20265e2e7ffc1b4cda0d94e27e86fb8bfe5b858766dd22988` |
| `backend/tests/test_agent.py` | tracked | 2854 | `e7a54959535edaedee4bd7de1da224391a81eebc757512515a03c74f63cfaad4` |
| `backend/tests/test_answer_composer.py` | tracked | 19023 | `44c06cf5648c5793cbcdd4b5d3dcfc7dadf5e4ad7344e1ad10d53940572b5ea3` |
| `backend/tests/test_config.py` | tracked | 1108 | `74279a01214f8f589ab65137373b68ffbad8f1734fb1d182545c0737f82d871f` |
| `backend/tests/test_epistemic_guard.py` | tracked | 14666 | `d666a2a1e504a815f9d4a7d723b4c373bb7628107fe86f3f6814ecc1e686abd0` |
| `backend/tests/test_evaluation_suite.py` | tracked | 16204 | `360ebe1e43daf90f99355cb99a5e6da1cde53bce9e60fe2d179e6d1d4ef5f030` |
| `backend/tests/test_evidence_contract.py` | tracked | 15998 | `bd4f1c47abbea130cf132c257c1e391dfa8b9e520a9c597a5a1f0c2b34e1cd8d` |
| `backend/tests/test_health.py` | tracked | 953 | `99457b7a814be8fe657a5cef2e9c350542f8c4a0ba477101acf31c1fa9691dbd` |
| `backend/tests/test_interpretation_engine.py` | tracked | 18835 | `5efeaec81f21871e1173e0387c29e0147eca14c01d3e9588018ff8b35df03ba2` |
| `backend/tests/test_patch1.py` | untracked | 15375 | `4f81a8198f948bf43c9e67a2979977e59cf46e7b6edc96fbd3e456bdabfc69a8` |
| `backend/tests/test_patch1_1.py` | untracked | 27240 | `c36f2bb67d1a998456856dc5fb0cd717d72750394288fe156092fc99bedb8ae9` |
| `backend/tests/test_phase_a.py` | tracked | 30477 | `7453e3141dce30a153ca53bd0805697b0c10cdc9db7915b5877ac1bbee4c1f41` |
| `backend/tests/test_phase_r.py` | tracked | 14905 | `9b861b9edb9ac5250ede52ad58f2026becb22b79f4630b1a5e2f50242314aa2e` |
| `backend/tests/test_phase_s.py` | tracked | 42046 | `69ccb143e6522ace78b9d061355fd94ad22d85165b862ba78e62c77e19cfd52a` |
| `backend/tests/test_phase_t.py` | untracked | 38232 | `9d98b490b76c632a91a71a4337d3c7f56e68c39da21e8da85633685372df2d80` |
| `backend/tests/test_phase_t1.py` | untracked | 16704 | `7c15cd8cd8b9d444a91dfc09c55c126309c8973bf60a18777cc2914993ce1140` |
| `backend/tests/test_philosophers.py` | tracked | 1378 | `d35dba07c5577c664c286c9367e46a3af570715d56bec3a98c2913954cc09dd0` |
| `backend/tests/test_security.py` | tracked | 5884 | `032f59540875db66388a4b54a95d983cf618d7e5e7b7448ec2d543eb19268d8b` |
| `backend/tests/test_thinking_events.py` | tracked | 3471 | `be4c0892cecff974cafead6444f790babf5e215690061890fcfa4f86e65e697d` |
| `backend/tool_contracts.py` | untracked | 38982 | `4136e24e2ca2e7a92dea8d02e3ed0ead58a1c7d4db64e286942ab3e4c7996024` |
| `backend/tools/__init__.py` | tracked | 28 | `45f8eaf61aa59b9ca834fe7732b011e84f887e639ed19e22c64d3571845febc9` |
| `backend/tools/build_book_json.py` | tracked | 12428 | `e571b396cebe3378aad5638d66525db1bc23a570f72e00cd4be47af5d1c4009b` |
| `backend/tools/build_covers_manifest.py` | tracked | 2227 | `43c5380f2a35ab71fba0d45cc96f0360b125c6dc895dbbdb57dc0cae17210e88` |
| `backend/tools/build_embeddings.py` | tracked | 4261 | `0757713f2574e232d99a23595cfb2dd2e53996748e10521cc17751b1a21033f5` |
| `backend/tools/build_philosopher_network.py` | tracked | 9323 | `1d568a7861c7ddceb6e06b9347f983ef4e37a5ac7ce233c9bd73ffab28057c43` |
| `backend/tools/download_gutenberg.py` | tracked | 5428 | `81ef856d22c1f88111ac1901d2a19c8c37b835132c00662d301cc13ad588b351` |
| `backend/tools/dp_build_nietzsche_index.py` | tracked | 5179 | `3e7028cb929c7f633c8a9e8cb1ef31fafa996d7a0a90a4605f027f12ad213953` |
| `backend/tools/dp_clean_book.py` | tracked | 48247 | `1e2b34bc5adeaa7788814c3ac7f2d19722ce191a1623226e395d017348245c68` |
| `backend/tools/dp_consistency_check.py` | tracked | 5288 | `cacd35f2624bf8aeadc1291b9289ce1adeefe30a32450167eb96c9379e659b7b` |
| `backend/tools/dp_embed_missing.py` | tracked | 5890 | `5f3db66fa2d306e568eb21e9054b1963e36f65a11a4b071bf339e6cdf88cf68d` |
| `backend/tools/dp_epub_covers.py` | tracked | 6438 | `d0f8907e17cf4de87b8171e54dd8b195a92ca529e29ed00657a378d17a61c683` |
| `backend/tools/dp_fix_authors.py` | tracked | 3304 | `9206e342330e23afdf520f967292a1083af483b54cdd6a7f2432413135f2e11e` |
| `backend/tools/dp_fix_catalog_chapters.py` | tracked | 994 | `efa93d9c9970e1400aa2a1c11d3f01653e3d041a67573b86a3d3469923a51e48` |
| `backend/tools/dp_gen_pdf_covers.py` | tracked | 4073 | `afb2abe8973dbc5a8f76f95dce29a01efcc79ac76adcea44749e9775f6e3e790` |
| `backend/tools/dp_gen_txt_covers.py` | tracked | 3847 | `903b29c8323004811a371b1f9abd54e2a99d498d078be23c1ac13d4c1c903d8b` |
| `backend/tools/dp_grab_cf_assets.py` | tracked | 8191 | `b75dc1545c7c1f2271d4c16734fa8dc6ce5fed5197c8d647733fd6bfddb56dbc` |
| `backend/tools/dp_import_epubs.py` | tracked | 7342 | `813097afcd7a7af7aebb28e6546a7608abea7e690eb88b1db6d86f3f95a2961a` |
| `backend/tools/dp_import_txt.py` | tracked | 6985 | `5ea23b25638f0d035de4790dee52974f81796cb127cc5f3fb6914560784972b9` |
| `backend/tools/dp_launch_ocr.py` | tracked | 2016 | `6b477180e01be902c5423ecab0ca36e9b5cdb1089a2e98e2afaee9f6460d0f3e` |
| `backend/tools/dp_merge_summaries.py` | tracked | 1661 | `f9f2f3b19354af68674b9699509034360d30c9b1b4929299c5e7ff85e1d9522b` |
| `backend/tools/dp_ocr_check.py` | tracked | 16374 | `fabb6d94c96e7af2d41d538aadc4e5c37905ab86bed8815d8b50cbb9efe0dc86` |
| `backend/tools/dp_ocr_epub.py` | tracked | 7361 | `99f03f1c9d3a272a045cd11f6ad1c93185dcb6b4d8ec2cca007a51781a560c6a` |
| `backend/tools/dp_ocr_watchdog.py` | tracked | 3539 | `01fe86bff1cf4a574bf77e48bebe89937077b9e101f77eb3746129659874d560` |
| `backend/tools/dp_pdf_import.py` | tracked | 20568 | `8424cd421ea1c9bd3ae3ccb1992147714c9eefee9fb376a9653c48fe81b394ea` |
| `backend/tools/dp_perf_phase_r.py` | tracked | 8384 | `d7f66cf56e88359342db982b665c090a8273afd0b492679a45979ea19956ac02` |
| `backend/tools/dp_retry_ocr.py` | tracked | 2804 | `21a2b0e246aee28da177b7a3a68d9f7caebb15dc6ec9f43b83e63abd288f709c` |
| `backend/tools/dp_run_import.py` | tracked | 12223 | `4267889b0fc36b000a774d369aa68b39c92802ca41481afb8c76b46bf84f683e` |
| `backend/tools/dp_score_books.py` | tracked | 4556 | `66cd3ccd0f340283bfe5d6d5f1b11a5ebe5310a22825bde8d67c0a9b40a6452c` |
| `backend/tools/dp_sync_all.py` | tracked | 3155 | `412d30c4930c830cb78a578a31b26272bffd627701c84c3c52c7e309f437b6da` |
| `backend/tools/dp_sync_books.py` | tracked | 12827 | `9bf7e85f4aa0e81c55db9f5457f4855f45572bb0655e82f71bac9f726c886967` |
| `backend/tools/dp_sync_fixed.py` | tracked | 5581 | `3db5e8c2db6159e18a9de450ab8c75da74750d8c0026229d39e4fe0597ed4714` |
| `backend/tools/dp_sync_oss_chapters.py` | tracked | 6054 | `dbad488f2f1ea5cb375b04a04e21e2b278f6ae1f06b609e6ee5239c990427c69` |
| `backend/tools/dp_sync_oss_images.py` | tracked | 5160 | `bb12da6fd70e4a46a416306b22dadf971dbddf636a6673a396ba9170569ffcf4` |
| `backend/tools/dp_sync_oss_static.py` | tracked | 7042 | `f77468656f91ace1152f6e86e6f2a75895e2b2058049bbc71c137f621679c13f` |
| `backend/tools/dp_toc_parts.py` | tracked | 3421 | `50be4c8b4599fe3f91d4332e26ecc04e971071517989a2725d29cabd53ac94ac` |
| `backend/tools/dp_uat_phase_a.py` | tracked | 12012 | `3beb8e83a31f36b72f4d2e4d33db42b645e2f0ab87e04a50d20ccba7ee2065ba` |
| `backend/tools/dp_uat_phase_r.py` | tracked | 8185 | `5010e6c299eb1a7f3cca1e1d2d091ec255a2f36a0b73d863d79fc5f32bbdb4fe` |
| `backend/tools/dp_verify_dual.py` | tracked | 4952 | `b45ab597d3b42fee321a641184261d093e6edfde44abddcf9cfa873c1d7eee91` |
| `backend/tools/gen_structure.py` | tracked | 20777 | `dc59704adffd20f81345cc199ef9b24f5ea8c0c9e85ee4f4d9ee1bdfa93607fd` |
| `backend/tools/gen_summaries.py` | tracked | 4869 | `05355b609724a3865f331b4b16928bcb77ab7191e747fb2ff5fed7ed79d69816` |
| `backend/tools/generate_catalog.py` | tracked | 4121 | `7daa0732a58025499ec03078fd2f0ab8b8f6b7a63a4ff1a720571566f86028d4` |
| `backend/tools/generate_worker_assets.py` | tracked | 4842 | `4a6a4e59463e5c812add2fdf71bb3fe50c27b7057aeff7282f8c475c9f35b886` |
| `backend/tools/migrate_users_to_d1.py` | tracked | 5251 | `0e6405df56efd028ed2a162abc822a6a63da2c381729e3ef8982099c1801669a` |
| `backend/tools/rebuild_auto.py` | tracked | 6548 | `7661452c126892bd9144e2032377d772adb2a63cc941ad18841d6499ec04d2e0` |
| `backend/tools/rebuild_spine.py` | tracked | 22005 | `cc8247167bb4caab88cf68bb4cf84e8b3c41fdf200e9c8a733d643455b541bd8` |
| `backend/tools/sync_full.py` | tracked | 4157 | `62583465a7a8a38c2ac6fbfdcffe2c55e5df2dd43afbcefb405bbb11b376ecfd` |
| `backend/tools/verify_book.py` | tracked | 5691 | `8277aa9916242a7c7cd5a5062fa55b6adbab4ad384856793d82495d8b8216634` |
| `docs/PHIAGENT_BACKEND_DECISION_AUTHORITY_MAP.md` | untracked | 19544 | `2e378447e91b087978310e1ec25c1d224953787088365e1203e38ece5c932e25` |
| `docs/PHIAGENT_BACKEND_DIAGNOSTIC.md` | untracked | 250708 | `769a9cfbd55cb9ba4fe4c8ab3caa1634f855196c3c9dabb3fee6cbfe32da413e` |
| `docs/PHIAGENT_BACKEND_FULL_ARCHITECTURE_AUDIT.md` | untracked | 58389 | `20544c59b505492af46eb2b53e2a02d2702547a428d730732e5aef7564fe2cb1` |
| `docs/PHIAGENT_BACKEND_PATCH1_1_REGRESSION.md` | untracked | 44190 | `b2ac8836172498caeb53325e9a7209cd629494d166e59c5d8cb116653628885c` |
| `docs/PHIAGENT_BACKEND_PATCH1_FINAL_GATE.md` | untracked | 113658 | `49051ef098010117763678fe861c24d813bae7a91626fec7eeeddbbb57fe8560` |
| `docs/PHIAGENT_BACKEND_PATCH1_REGRESSION.md` | untracked | 48888 | `7cb60c6ec1e5be3c7ee32ad2de8c08f655ff5ba5ac6d757cdc5d453fb0732f01` |
| `docs/PHIAGENT_BACKEND_QUALITY_GATE2.md` | untracked | 196836 | `7c32f9245da65271b0c7729933a21b4a5cffc8a22c701f6983a6901b18740006` |
| `docs/PHIAGENT_PHASE_T1_SOURCE_VERIFICATION_REGRESSION.md` | untracked | 17830 | `81dbaef6fc72ac87d0663e4b0f010f1df8ad44f601a921f0cb2fb022c46e4d25` |
| `docs/PHIAGENT_PHASE_T_REGRESSION.md` | untracked | 14197 | `ba989e5d1be9737b23a8cad5de42a7f64e31d6406ebe904f687d18a0812bba21` |
| `docs/PHIAGENT_PHASE_T_TOOL_ARCHITECTURE.md` | untracked | 8776 | `288e42cde0ebdbcdc2d0fbccad89d7332b9d1fe08ec704877f285f64efcfb9ce` |
| `docs/PHIAGENT_TOOL_ARCHITECTURE.md` | untracked | 10790 | `1098c337678bd12de7af96213d5768278a779e1a956abbf3b869d33f2be1b761` |

## 5. 规范化 manifest（canonical bytes 原文）

```
5f041a917482899433ab5eedcdd3e03d2edf8091886828fc418217f56bcd8075  backend/__init__.py
b7d2868992bd84cffb57ad2be1d97e10a0e080a332feb59319613ee6fdca7559  backend/admin.py
01f173f156102f1aa643f1e99ebcb9a37aa2d3b21900892e3bd8a56a85019470  backend/agent_runtime.py
0c4c18aa5b914a3eac94e4de3f9b8e3dc507ec60652fd49324f4480afdc8f580  backend/agents.py
7dc028e4ce1d1a8b0563416a8c523366bbf6589fa921fab368a4e21395b25211  backend/answer_composer.py
a1165a72c4be2b1991d29d1a9ac97cb85052912f65278bed2b987a09018d745a  backend/auth.py
bc76bd7356a2d96c1df015931972caf26c6e0d80790ed0ff82df67770009feae  backend/auth_deps.py
9a4994514b96feefebafa8be3c3b55230b698a6ecc1749a4937f9e06db1b55d4  backend/config.py
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  backend/data/__init__.py
6ffba7224e0ff922e9c9e25ce4268b0cfbaadb89fd78dbc9b1ebf83803bebb8e  backend/db.py
1b112c6b99bbe0210a5f04778fabfdb91f81121d385e5e76d3e078c378695a62  backend/drawio_convert.py
f642fc3282f434fd79871f7c07f07247d7233d87e1a157de748650046b2c8fc6  backend/engine_langgraph.py
3a157fa0f72e8ddee5c529478c08dcd49e45f7aac8ae16de1170dc787d01e98f  backend/epistemic_guard.py
e77763f957a631440df2f4ea9e8c85629bdf6d8cb2f1e8915bf706fb96a36ce0  backend/eval_agent.py
3bebbb87e9a284f3275b8c77922d4771b59036a4c84c29987582c22df1bab063  backend/evaluation_suite.py
2c3bcccd6242c84b794d1175030984097b549c92f625e1e5c9f8c893216dd83d  backend/evidence_contract.py
570e0eb7f37c96ccb813ebcabcacd8833c97ae082ff60f33157911fa4347f66b  backend/fix_bios.py
6d445566eddb8c0f9bf86a1583358849abf699d962306c6de832f69656c27df7  backend/guard.py
271806191766d1483f63c3c8522362b07112b06fa40d47eb35af666fd9b27764  backend/interpretation_engine.py
9e1602f1180bcba5f3d0e02ba376a98e41c347ec3bf13f13be7eed8b13f81c9e  backend/main.py
91d8b9f3846744591fbe6ad28ce7532b8e5bbbaaa1f1c765b463649e0fab984f  backend/mcp_client.py
35d34c95f4efbddc994d3525d505a3807dbec7f8638dceddd87aefa7b0c649dc  backend/mcp_servers/demo_server.py
5d260061515d0a7eb018e873e304fd07e6642ba442f91d5b911fc4232fcde546  backend/mcp_servers/phiagent.py
42e2b7af7e1902be3b3ea07ed03812928c92adf14e5da8d76435f6315c9b877a  backend/models/__init__.py
f3a1aad10a0154f4b64bc38ad90338ccbc3680bc3fa011555d4a426a74e2ff4a  backend/modules/__init__.py
fb684ac51f8f4c6e3d0d365a1e617eba01ed8af9d0ce7d0374c750c1b5dbb72f  backend/modules/document_loader.py
2dce8f6797cb9955b3ba2ef1761f7855e77c1c3e0de5ca755e18d8d553ca9ee7  backend/modules/embedding.py
b4af81d670e2bcdf6506275a7b569a320ed4d5c2bdcc3209febe7f6a255edd7f  backend/modules/llm_client.py
4df1ab5e491e0282a82cd5b94f4b714d9fdd379f68dd7d97fc83c1d4de56936a  backend/modules/ocr_engine.py
21fc73113675ff1c1034b3f8bb16baa66f617ec99500bb4b80f2cc60dcbebbf4  backend/modules/rag_chain.py
fc34935bd5a1b58d02b4fbd2823969083af9a03365d01f4d28b62456ed571a91  backend/modules/text_processor.py
f6e74acfeea75564ef86c2b40453e29a83d784aff4d7501dcbbc747d64fdca79  backend/modules/vector_store.py
993ec8b110c0577217d3fd51f66a0d21c5311773f8ab83cc28c1272d6bbbd0d9  backend/philo_retrieval.py
3c0b88c1e237c9a41e466742bfb4d2caee9581d73dae34793ac6b3faa2efca13  backend/quote_bound.py
7c68b0ec67a83a0d5c2d22da1f7c307a2d29dae4e8d0e9e871e3ce389604e2a1  backend/reasoning_plan.py
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  backend/routes/__init__.py
19c3337f2530e3b204a403595768ed2fe475b37ae775ebf4dcfe02c11639919d  backend/routes/account.py
661a8393e7c7e568203b56fe41f7e38bb5631ef7e6daf2fc1b24a0fe01075a5d  backend/routes/admin_routes.py
74796464122a86f33f189ea4afdf9424a58d7fcc609981bf83de474c85d4d249  backend/routes/agent.py
408699acbaf8e739d6f66acc06d79c0f3f05be1af964ee779587fc1d59fad1e7  backend/routes/agent_core.py
7529d1893c822d16e66d3087e07b2f2e4eeab3e2da9bc64ae62043e27604e086  backend/routes/agent_llm.py
9c29adc78d36ae3da1e9622a95e97ab2fff7a65ae951499914da93b4b76d4fa7  backend/routes/agent_sse.py
bc38592b693e3c3de80e493264d6d1eb58f0f9e1b4da80b340fa96bb9591c0d4  backend/routes/agent_tools_eval.py
757dffaf617b4de1691bc9d5784f7d84fe4f5259f9e3c84d9143146abe4331c7  backend/routes/agent_tools_memory.py
17a5f7ca8f767f2e172c59b288cc7529d88322ffd4b3d44e8e7e685ed6920753  backend/routes/agent_tools_retrieval.py
2e71b51a4aaf1ad462bdb787082251e1c6ce2b28bf6c3093e542bb3d63ef0b6e  backend/routes/ai.py
766df1b3228ae224254594865b2bf4e338aec72b8b33540a57528afb76d091fc  backend/routes/auth_routes.py
76ba7495e214bcb51f66ec9348903824f6b137f6129b8041ebf3861108996183  backend/routes/authors.py
d5c8703f081a73b7085c240bba10bf517a32f8d856f513be4dd05a85415eb226  backend/routes/books.py
706375f3f2dcf082418607e521a6b34a91c1d66ce85fa78201c3787c694ff8b9  backend/routes/health.py
58ef9dae88654571099dc411571a3ce6343e1aa44f9000cb9d60610c5baf29e5  backend/routes/history.py
ef2c156efee42ccf589b7a0d41aef10a7499507e42509065a42aa88783ff0492  backend/routes/knowledge.py
a21dbe9c72f0cedaac176afcccf9f7fa5bcd6a074dd0c2e559eb8af3629c024a  backend/routes/openai_compat.py
59facba450aab1ef2cc5704d2b48fd807145eeb0c9e39dc890788bc7e168f1ce  backend/routes/sync.py
2e5674aa641fec078f03cdeff5d01aed4f5726d3a68175065b8ee3f39fedce4d  backend/routes/text.py
16dc5220ab198835a6c4dc4898f55910e09bfe7127608a7bdfc840a534f2140e  backend/routes/upload.py
3fa554db9ae3746df45a544120769e756ace380142525336da61120ddcec355a  backend/routes/user.py
746db97f17390a104ec97c792f89479ed9764d5db283ab1a575914be1db057df  backend/semantic_obligations.py
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  backend/services/__init__.py
4b640c20b223f182ee9fc1f1ed416e79059f009d43086761ab94da6da3a117d8  backend/services/book_scanner.py
fe1d69710883ae5423aae76b8e5910d2efef630855d39d4a8ccc12e45e0a535e  backend/services/summaries.py
a72fd3687d4ee420e7ee450744be452f409b3969f893e8a9b99c730de0fecbd1  backend/services/tag_utils.py
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  backend/tests/__init__.py
85f3413e2baf7bd20265e2e7ffc1b4cda0d94e27e86fb8bfe5b858766dd22988  backend/tests/regression_oldman_sea.py
e7a54959535edaedee4bd7de1da224391a81eebc757512515a03c74f63cfaad4  backend/tests/test_agent.py
44c06cf5648c5793cbcdd4b5d3dcfc7dadf5e4ad7344e1ad10d53940572b5ea3  backend/tests/test_answer_composer.py
74279a01214f8f589ab65137373b68ffbad8f1734fb1d182545c0737f82d871f  backend/tests/test_config.py
d666a2a1e504a815f9d4a7d723b4c373bb7628107fe86f3f6814ecc1e686abd0  backend/tests/test_epistemic_guard.py
360ebe1e43daf90f99355cb99a5e6da1cde53bce9e60fe2d179e6d1d4ef5f030  backend/tests/test_evaluation_suite.py
bd4f1c47abbea130cf132c257c1e391dfa8b9e520a9c597a5a1f0c2b34e1cd8d  backend/tests/test_evidence_contract.py
99457b7a814be8fe657a5cef2e9c350542f8c4a0ba477101acf31c1fa9691dbd  backend/tests/test_health.py
5efeaec81f21871e1173e0387c29e0147eca14c01d3e9588018ff8b35df03ba2  backend/tests/test_interpretation_engine.py
4f81a8198f948bf43c9e67a2979977e59cf46e7b6edc96fbd3e456bdabfc69a8  backend/tests/test_patch1.py
c36f2bb67d1a998456856dc5fb0cd717d72750394288fe156092fc99bedb8ae9  backend/tests/test_patch1_1.py
7453e3141dce30a153ca53bd0805697b0c10cdc9db7915b5877ac1bbee4c1f41  backend/tests/test_phase_a.py
9b861b9edb9ac5250ede52ad58f2026becb22b79f4630b1a5e2f50242314aa2e  backend/tests/test_phase_r.py
69ccb143e6522ace78b9d061355fd94ad22d85165b862ba78e62c77e19cfd52a  backend/tests/test_phase_s.py
9d98b490b76c632a91a71a4337d3c7f56e68c39da21e8da85633685372df2d80  backend/tests/test_phase_t.py
7c15cd8cd8b9d444a91dfc09c55c126309c8973bf60a18777cc2914993ce1140  backend/tests/test_phase_t1.py
d35dba07c5577c664c286c9367e46a3af570715d56bec3a98c2913954cc09dd0  backend/tests/test_philosophers.py
032f59540875db66388a4b54a95d983cf618d7e5e7b7448ec2d543eb19268d8b  backend/tests/test_security.py
be4c0892cecff974cafead6444f790babf5e215690061890fcfa4f86e65e697d  backend/tests/test_thinking_events.py
4136e24e2ca2e7a92dea8d02e3ed0ead58a1c7d4db64e286942ab3e4c7996024  backend/tool_contracts.py
45f8eaf61aa59b9ca834fe7732b011e84f887e639ed19e22c64d3571845febc9  backend/tools/__init__.py
e571b396cebe3378aad5638d66525db1bc23a570f72e00cd4be47af5d1c4009b  backend/tools/build_book_json.py
43c5380f2a35ab71fba0d45cc96f0360b125c6dc895dbbdb57dc0cae17210e88  backend/tools/build_covers_manifest.py
0757713f2574e232d99a23595cfb2dd2e53996748e10521cc17751b1a21033f5  backend/tools/build_embeddings.py
1d568a7861c7ddceb6e06b9347f983ef4e37a5ac7ce233c9bd73ffab28057c43  backend/tools/build_philosopher_network.py
81ef856d22c1f88111ac1901d2a19c8c37b835132c00662d301cc13ad588b351  backend/tools/download_gutenberg.py
3e7028cb929c7f633c8a9e8cb1ef31fafa996d7a0a90a4605f027f12ad213953  backend/tools/dp_build_nietzsche_index.py
1e2b34bc5adeaa7788814c3ac7f2d19722ce191a1623226e395d017348245c68  backend/tools/dp_clean_book.py
cacd35f2624bf8aeadc1291b9289ce1adeefe30a32450167eb96c9379e659b7b  backend/tools/dp_consistency_check.py
5f3db66fa2d306e568eb21e9054b1963e36f65a11a4b071bf339e6cdf88cf68d  backend/tools/dp_embed_missing.py
d0f8907e17cf4de87b8171e54dd8b195a92ca529e29ed00657a378d17a61c683  backend/tools/dp_epub_covers.py
9206e342330e23afdf520f967292a1083af483b54cdd6a7f2432413135f2e11e  backend/tools/dp_fix_authors.py
efa93d9c9970e1400aa2a1c11d3f01653e3d041a67573b86a3d3469923a51e48  backend/tools/dp_fix_catalog_chapters.py
afb2abe8973dbc5a8f76f95dce29a01efcc79ac76adcea44749e9775f6e3e790  backend/tools/dp_gen_pdf_covers.py
903b29c8323004811a371b1f9abd54e2a99d498d078be23c1ac13d4c1c903d8b  backend/tools/dp_gen_txt_covers.py
b75dc1545c7c1f2271d4c16734fa8dc6ce5fed5197c8d647733fd6bfddb56dbc  backend/tools/dp_grab_cf_assets.py
813097afcd7a7af7aebb28e6546a7608abea7e690eb88b1db6d86f3f95a2961a  backend/tools/dp_import_epubs.py
5ea23b25638f0d035de4790dee52974f81796cb127cc5f3fb6914560784972b9  backend/tools/dp_import_txt.py
6b477180e01be902c5423ecab0ca36e9b5cdb1089a2e98e2afaee9f6460d0f3e  backend/tools/dp_launch_ocr.py
f9f2f3b19354af68674b9699509034360d30c9b1b4929299c5e7ff85e1d9522b  backend/tools/dp_merge_summaries.py
fabb6d94c96e7af2d41d538aadc4e5c37905ab86bed8815d8b50cbb9efe0dc86  backend/tools/dp_ocr_check.py
99f03f1c9d3a272a045cd11f6ad1c93185dcb6b4d8ec2cca007a51781a560c6a  backend/tools/dp_ocr_epub.py
01fe86bff1cf4a574bf77e48bebe89937077b9e101f77eb3746129659874d560  backend/tools/dp_ocr_watchdog.py
8424cd421ea1c9bd3ae3ccb1992147714c9eefee9fb376a9653c48fe81b394ea  backend/tools/dp_pdf_import.py
d7f66cf56e88359342db982b665c090a8273afd0b492679a45979ea19956ac02  backend/tools/dp_perf_phase_r.py
21a2b0e246aee28da177b7a3a68d9f7caebb15dc6ec9f43b83e63abd288f709c  backend/tools/dp_retry_ocr.py
4267889b0fc36b000a774d369aa68b39c92802ca41481afb8c76b46bf84f683e  backend/tools/dp_run_import.py
66cd3ccd0f340283bfe5d6d5f1b11a5ebe5310a22825bde8d67c0a9b40a6452c  backend/tools/dp_score_books.py
412d30c4930c830cb78a578a31b26272bffd627701c84c3c52c7e309f437b6da  backend/tools/dp_sync_all.py
9bf7e85f4aa0e81c55db9f5457f4855f45572bb0655e82f71bac9f726c886967  backend/tools/dp_sync_books.py
3db5e8c2db6159e18a9de450ab8c75da74750d8c0026229d39e4fe0597ed4714  backend/tools/dp_sync_fixed.py
dbad488f2f1ea5cb375b04a04e21e2b278f6ae1f06b609e6ee5239c990427c69  backend/tools/dp_sync_oss_chapters.py
bb12da6fd70e4a46a416306b22dadf971dbddf636a6673a396ba9170569ffcf4  backend/tools/dp_sync_oss_images.py
f77468656f91ace1152f6e86e6f2a75895e2b2058049bbc71c137f621679c13f  backend/tools/dp_sync_oss_static.py
50be4c8b4599fe3f91d4332e26ecc04e971071517989a2725d29cabd53ac94ac  backend/tools/dp_toc_parts.py
3beb8e83a31f36b72f4d2e4d33db42b645e2f0ab87e04a50d20ccba7ee2065ba  backend/tools/dp_uat_phase_a.py
5010e6c299eb1a7f3cca1e1d2d091ec255a2f36a0b73d863d79fc5f32bbdb4fe  backend/tools/dp_uat_phase_r.py
b45ab597d3b42fee321a641184261d093e6edfde44abddcf9cfa873c1d7eee91  backend/tools/dp_verify_dual.py
dc59704adffd20f81345cc199ef9b24f5ea8c0c9e85ee4f4d9ee1bdfa93607fd  backend/tools/gen_structure.py
05355b609724a3865f331b4b16928bcb77ab7191e747fb2ff5fed7ed79d69816  backend/tools/gen_summaries.py
7daa0732a58025499ec03078fd2f0ab8b8f6b7a63a4ff1a720571566f86028d4  backend/tools/generate_catalog.py
4a6a4e59463e5c812add2fdf71bb3fe50c27b7057aeff7282f8c475c9f35b886  backend/tools/generate_worker_assets.py
0e6405df56efd028ed2a162abc822a6a63da2c381729e3ef8982099c1801669a  backend/tools/migrate_users_to_d1.py
7661452c126892bd9144e2032377d772adb2a63cc941ad18841d6499ec04d2e0  backend/tools/rebuild_auto.py
cc8247167bb4caab88cf68bb4cf84e8b3c41fdf200e9c8a733d643455b541bd8  backend/tools/rebuild_spine.py
62583465a7a8a38c2ac6fbfdcffe2c55e5df2dd43afbcefb405bbb11b376ecfd  backend/tools/sync_full.py
8277aa9916242a7c7cd5a5062fa55b6adbab4ad384856793d82495d8b8216634  backend/tools/verify_book.py
2e378447e91b087978310e1ec25c1d224953787088365e1203e38ece5c932e25  docs/PHIAGENT_BACKEND_DECISION_AUTHORITY_MAP.md
769a9cfbd55cb9ba4fe4c8ab3caa1634f855196c3c9dabb3fee6cbfe32da413e  docs/PHIAGENT_BACKEND_DIAGNOSTIC.md
20544c59b505492af46eb2b53e2a02d2702547a428d730732e5aef7564fe2cb1  docs/PHIAGENT_BACKEND_FULL_ARCHITECTURE_AUDIT.md
b2ac8836172498caeb53325e9a7209cd629494d166e59c5d8cb116653628885c  docs/PHIAGENT_BACKEND_PATCH1_1_REGRESSION.md
49051ef098010117763678fe861c24d813bae7a91626fec7eeeddbbb57fe8560  docs/PHIAGENT_BACKEND_PATCH1_FINAL_GATE.md
7cb60c6ec1e5be3c7ee32ad2de8c08f655ff5ba5ac6d757cdc5d453fb0732f01  docs/PHIAGENT_BACKEND_PATCH1_REGRESSION.md
7c32f9245da65271b0c7729933a21b4a5cffc8a22c701f6983a6901b18740006  docs/PHIAGENT_BACKEND_QUALITY_GATE2.md
81dbaef6fc72ac87d0663e4b0f010f1df8ad44f601a921f0cb2fb022c46e4d25  docs/PHIAGENT_PHASE_T1_SOURCE_VERIFICATION_REGRESSION.md
ba989e5d1be9737b23a8cad5de42a7f64e31d6406ebe904f687d18a0812bba21  docs/PHIAGENT_PHASE_T_REGRESSION.md
288e42cde0ebdbcdc2d0fbccad89d7332b9d1fe08ec704877f285f64efcfb9ce  docs/PHIAGENT_PHASE_T_TOOL_ARCHITECTURE.md
1098c337678bd12de7af96213d5768278a779e1a956abbf3b869d33f2be1b761  docs/PHIAGENT_TOOL_ARCHITECTURE.md
```

（上方代码块内容 = 141 行，每行 `<sha256>  <path>`；本节仅省略了末行换行符以渲染，
  计算以实际 bytes 为准：每行均以 `
` 结尾，共 13685 bytes。）

## 6. 结果

```
MANIFEST_SHA256 = 45ffe862c8b088e5303ac44b84bd1bb8ced48645a9ca90d6d03d1fb5b2d28769
```

## 7. 复核方法（任意时刻可重算）

```bash
# 在 repo 根目录，对范围内每个文件: sha256sum <file>
# 按 path 排序拼接 "<sha256>  <path>
" 后: sha256sum
# 结果必须等于 MANIFEST_SHA256；任一文件变动/增删都会使其改变（基线漂移检测）。
```

---

## 8. RE-VERIFICATION NOTE（2026-09-04 17:45–17:55 第二遍独立重算）

O0-R 第二遍复核以全新脚本独立重算本清单（不信任初版中间产物）：
全新遍历 `backend/**/*.py`（排除 `__pycache__`/`_tmp`/`.pytest_cache`）+ `docs/PHIAGENT_*.md`
（按名排除本 Gate 两份输出文档），UTF-8 码点序排序后按第 3 节算法拼装：

- 条目数 **141**（tracked 123 / untracked 18）— 与初版一致
- manifest bytes = 13,685
- **MANIFEST_SHA256 = `45ffe862c8b088e5303ac44b84bd1bb8ced48645a9ca90d6d03d1fb5b2d28769` — 与初版完全一致**
- 本文档第 4 节表格的 141 行逐行与活树实时 sha256/size 机器比对：**0 mismatch**，无漂移

结论：自初版生成以来，清单范围内 141 个文件无一变动；本清单当前仍精确描述基线。
