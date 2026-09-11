# Backend implementation order

1. Start FastAPI and check /api/health.
2. Register/login a farmer.
3. Create a farm.
4. Register a resource-owner and create machinery.
5. Create a resource request.
6. Check the 0–100 priority explanation.
7. Generate feasible slots.
8. Confirm a booking.
9. Attempt an overlapping booking and demonstrate the 409 conflict.
10. Trigger a breakdown/weather disruption and demonstrate reallocation.
11. Open dashboard endpoints.
12. Test offline sync.
13. Configure weather API.
14. Train fertilizer model using validated data.
15. Train pesticide model using validated data.
16. Add labour providers and labour requests.
17. Add buyer orders and farmer sell/ignore responses.
