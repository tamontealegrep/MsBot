"""
SSL Certificate Generator for Local Development
Generates self-signed certificates for HTTPS local server
"""

import os
import subprocess
import sys
from pathlib import Path

def create_ssl_certificates():
    """Generate self-signed SSL certificates for local development"""
    
    # Create certs directory
    certs_dir = Path("./certs")
    certs_dir.mkdir(exist_ok=True)
    
    cert_path = certs_dir / "cert.pem"
    key_path = certs_dir / "key.pem"
    
    # Check if certificates already exist
    if cert_path.exists() and key_path.exists():
        print("✅ SSL certificates already exist")
        return True
    
    print("🔐 Generating SSL certificates for local development...")
    
    try:
        # Generate private key and certificate
        cmd = [
            "openssl", "req", "-x509", "-newkey", "rsa:4096",
            "-keyout", str(key_path),
            "-out", str(cert_path),
            "-days", "365",
            "-nodes",
            "-subj", "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ SSL certificates generated successfully!")
            print(f"   Certificate: {cert_path}")
            print(f"   Private Key: {key_path}")
            print("\n⚠️  Note: These are self-signed certificates for development only.")
            print("   Your browser will show a security warning - this is normal.")
            return True
        else:
            print(f"❌ Error generating certificates: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ OpenSSL not found. Please install OpenSSL:")
        print("   - Windows: Download from https://slproweb.com/products/Win32OpenSSL.html")
        print("   - macOS: brew install openssl")
        print("   - Linux: sudo apt-get install openssl (Ubuntu/Debian)")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def setup_ngrok_info():
    """Display ngrok setup information"""
    print("\n🌐 For external access (Teams webhook from internet):")
    print("   1. Install ngrok: https://ngrok.com/download")
    print("   2. Run: ngrok http 3978")
    print("   3. Use the HTTPS URL provided by ngrok in your Teams App configuration")
    print("   4. Update your Teams App messaging endpoint to: https://your-ngrok-url.ngrok.io/api/messages")

if __name__ == "__main__":
    print("MSBot SSL Setup")
    print("===============")
    
    success = create_ssl_certificates()
    
    if success:
        setup_ngrok_info()
        print("\n✅ SSL setup complete! You can now run the bot with HTTPS enabled.")
    else:
        print("\n❌ SSL setup failed. Check the errors above.")
        sys.exit(1)