class VerifyOTPView(APIView):
    def post(self, request):
        device_id = request.data.get('device_id')  # Từ CreateQRView
        otp_code = request.data.get('otp_code')    # User nhập: "123456"
        
        # Bước 1: Tìm thiết bị chưa xác nhận
        device = TOTPDevice.objects.get(
            id=device_id,
            user=request.user,
            confirmed=False  # ← Chỉ thiết bị chưa xác nhận
        )
        
        # Bước 2: Kiểm tra OTP code có đúng không
        if device.verify_token(otp_code):  # Kiểm tra "123456"
            # Bước 3: Đánh dấu thiết bị đã xác nhận
            device.confirmed = True  # ← Quan trọng: BẬT 2FA
            device.save()
            
            return {"message": "2FA enabled successfully!"}
        else:
            return {"error": "Wrong OTP code"}