"""
Setup Profile Pictures Directory and Default Profile Image

This script ensures that:
1. The profile_pics directory exists in the static folder
2. A default profile image exists

Run this script once to set up the necessary directory structure for profile pictures.
"""

import os
import sys
from PIL import Image, ImageDraw

def setup_profile_pics_directory():
    """Create profile_pics directory and default profile image"""
    try:
        # Determine the app path
        from app import create_app
        app = create_app()
        
        with app.app_context():
            # Path for profile pictures
            profile_pics_dir = os.path.join(app.root_path, 'static', 'profile_pics')
            
            # Create directory if it doesn't exist
            if not os.path.exists(profile_pics_dir):
                print(f"Creating directory: {profile_pics_dir}")
                os.makedirs(profile_pics_dir)
            else:
                print(f"Directory already exists: {profile_pics_dir}")
            
            # Create a default profile image if it doesn't exist
            default_img_path = os.path.join(profile_pics_dir, 'default.jpg')
            if not os.path.exists(default_img_path):
                print("Creating default profile image...")
                
                # Create a simple default avatar (blue circle with white background)
                size = 200
                img = Image.new('RGB', (size, size), color=(255, 255, 255))
                d = ImageDraw.Draw(img)
                
                # Draw a colored circle
                circle_color = (65, 105, 225)  # Royal blue
                d.ellipse((25, 25, size-25, size-25), fill=circle_color)
                
                # Add a simple user silhouette in the middle
                d.ellipse((80, 65, 120, 105), fill=(255, 255, 255))  # Head
                d.rectangle((65, 125, 135, 175), fill=(255, 255, 255))  # Body
                
                # Save the image
                img.save(default_img_path)
                print(f"Default profile image created at: {default_img_path}")
            else:
                print(f"Default profile image already exists at: {default_img_path}")
            
            print("Profile pictures setup completed successfully!")
    except Exception as e:
        print(f"Error setting up profile pictures: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Setting up profile pictures directory and default image...")
    if setup_profile_pics_directory():
        print("Setup completed successfully!")
    else:
        print("Setup failed. Please check the error messages above.")
        sys.exit(1)