# /testcase-impact — Khoanh case cần retest khi code đổi

## Dùng
```
/testcase-impact <folder> <symbol1> [symbol2 …]
```
Ví dụ: `/testcase-impact wtf-is-this/TestCase_No.10.4 ProBackendSyncService.sync_customer_upserted`

## Chạy
```bash
source venv/bin/activate
python -c "from qa.impact import affected; print(affected('<folder>', ['<symbol>']))"
```
Kết quả = list TC → đưa vào `/testcase-retest <folder> <TC…>` của pipeline sếp.
