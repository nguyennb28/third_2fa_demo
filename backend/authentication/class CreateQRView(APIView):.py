class CreateQRView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user
            
            # Xóa device cũ chưa confirm
            TOTPDevice.objects.filter(user=user, confirmed=False).delete()
            
            # Kiểm tra user đã có 2FA chưa
            existing_device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
            if existing_device:
                return Response({
                    'error': True,
                    'message': '2FA is already enabled for this user',
                    'has_2fa': True
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Tạo device mới
            device = TOTPDevice.objects.create(
                user=user,
                name=f'{user.username}-device',
                confirmed=False
            )
            
            # Tạo QR code
            qr_url = device.config_url
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return Response({
                'success': True,
                'message': 'QR code generated successfully',
                'data': {
                    'qr_code': f"data:image/png;base64,{img_base64}",
                    'device_id': device.id,
                    'secret': device.bin_key.hex(),
                    'instructions': 'Scan this QR code with Google Authenticator app'
                }
            })
            
        except Exception as e:
            return Response({
                'error': True,
                'message': 'Failed to generate QR code',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VerifyOTPView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            device_id = request.data.get('device_id')
            otp_code = request.data.get('otp_code', '').strip()
            
            # Validation
            if not device_id:
                return Response({
                    'error': True,
                    'message': 'Device ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            if not otp_code:
                return Response({
                    'error': True,
                    'message': 'OTP code is required'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            if len(otp_code) != 6 or not otp_code.isdigit():
                return Response({
                    'error': True,
                    'message': 'OTP code must be 6 digits'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Tìm device
            try:
                device = TOTPDevice.objects.get(
                    id=device_id,
                    user=request.user,
                    confirmed=False
                )
            except TOTPDevice.DoesNotExist:
                return Response({
                    'error': True,
                    'message': 'Device not found or already confirmed'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Verify OTP
            if device.verify_token(otp_code):
                device.confirmed = True
                device.save()
                
                return Response({
                    'success': True,
                    'message': '2FA has been enabled successfully',
                    'data': {
                        'has_2fa': True,
                        'device_name': device.name
                    }
                })
            else:
                return Response({
                    'error': True,
                    'message': 'Invalid OTP code. Please try again.',
                    'hint': 'Make sure you are using the latest code from Google Authenticator'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'error': True,
                'message': 'Failed to verify OTP',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)