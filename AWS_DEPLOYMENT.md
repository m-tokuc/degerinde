# AWS EC2 Deployment Guide ☁️

This guide will walk you through launching our End-to-End MLOps Car Pricing Engine on an Amazon Web Services (AWS) EC2 virtual server.

## Step 1: Launch the EC2 Instance
1. Log in to your **AWS Management Console**.
2. Navigate to the **EC2 Dashboard** and click **Launch Instance**.
3. **Name**: `car-pricing-engine`.
4. **AMI (Amazon Machine Image)**: Select **Ubuntu Server 22.04 LTS**.
5. **Instance Type**: Select `t2.medium` (Recommended) or `t2.micro` (Free tier, but might struggle with ML compiling depending on RAM).
6. **Key Pair**: Create a new key pair (e.g., `car-engine-key.pem`) and download it. You will need this to SSH into the server.

## Step 2: Configure the Security Group (Firewall)
In the "Network Settings" section of the EC2 launch page, click **Edit** and add the following **Inbound Rules**:

| Type | Protocol | Port Range | Source | Description |
| :--- | :--- | :--- | :--- | :--- |
| SSH | TCP | `22` | Anywhere (`0.0.0.0/0`) | For terminal access |
| Custom TCP | TCP | `3000` | Anywhere (`0.0.0.0/0`) | Next.js Frontend |
| Custom TCP | TCP | `8000` | Anywhere (`0.0.0.0/0`) | FastAPI Backend |

> [!WARNING]
> If you do not open ports 3000 and 8000, your containers will run on the server, but you will not be able to access the web interface or API from the outside world!

## Step 3: Connect to the Server (SSH)
Once the instance is running, copy its **Public IPv4 address**.
Open your local terminal and run:

```bash
# Secure your key file (only do this once)
chmod 400 ~/Downloads/car-engine-key.pem

# Connect to the server
ssh -i "~/Downloads/car-engine-key.pem" ubuntu@<YOUR_EC2_PUBLIC_IP>
```

## Step 4: Clone the Project and Deploy
Inside your EC2 terminal, run the following commands:

```bash
# 1. Clone your repository (Replace with your actual GitHub URL)
git clone https://github.com/your-username/car_project.git
cd car_project

# 2. Make the deployment script executable
chmod +x deploy.sh

# 3. Run the automated deployment script
./deploy.sh
```

## Step 5: Test the Live Application!
- **Frontend (UI)**: Open your browser and go to `http://<YOUR_EC2_PUBLIC_IP>:3000`
- **Backend (API)**: Open your browser and go to `http://<YOUR_EC2_PUBLIC_IP>:8000/docs`

> [!TIP]
> The database will start completely empty. Because we designed the FastAPI app to auto-generate the schema, it won't crash. To get dynamic dropdown options in the frontend, you will need to restore your SQL backup or run a data scraper script on the server.
