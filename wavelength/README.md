# Using Wavelenght zone

```
# 1. create (if not already created) vpc.

# 2. create cagw and attacht to vpc
aws ec2 create-carrier-gateway --vpc-id vpc-02a64fd21ad8703da

# 3. create route table

# 4. associate the rule to the rtb using the cagw (carrier gateway)
aws ec2 create-route --route-table-id rtb-0ff4645a811ef15e5 --destination-cidr-block 0.0.0.0/0 --carrier-gateway-id cagw-0c811c8a95732a357

# 5. associate the rtb to the subnet
aws ec2 associate-route-table --subnet-id <your-subnet-id> --route-table-id <your-route-table-id>

# 6. describe info of cagw
aws ec2 describe-carrier-gateways

# 7. create ec2 instance
# NOTA: gp3 and magnetic (standard) root volume is not supported in wvl zone
aws ec2 run-instances --region eu-west-3 \
    --network-interfaces "DeviceIndex=0,AssociateCarrierIpAddress=true,SubnetId=subnet-0e02e81f26f3291d6" \
    --image-id ami-04a92520784b93e73 --instance-type t3.medium \
    --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":10,"VolumeType":"gp2"}}]' \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=ec2-wvl}]' \
    --key-name tactile5g \
    --iam-instance-profile Name=ec2-edge-20240906094442237200000001

# example including security group:
aws ec2 run-instances --region eu-west-3 \
    --network-interfaces "DeviceIndex=0,AssociateCarrierIpAddress=true,SubnetId=subnet-053889d9c078138a1,Groups=sg-0e2dcc06c273036d1" \
    --image-id ami-04a92520784b93e73 --instance-type t3.medium \
    --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":80,"VolumeType":"gp2"}}]' \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=cluster-researcher-worker-2}]' \
    --key-name researcher-aws \
    --iam-instance-profile Name=cluster-researcher-worker-1-20250328112848949700000009

## if issues with iam-instance-profile
aws iam list-instance-profiles
### if ima instance profile not created:
aws iam create-instance-profile --instance-profile-name ec2-edge-20240906094442237200000001
# add role to the instance profile
aws iam add-role-to-instance-profile --instance-profile-name ec2-edge-20240906094442237200000001 --role-name MY_ROLE


```
# Clean environment

```
# delete cagw
aws ec2 delete-carrier-gateway --carrier-gateway-id cagw-0c811c8a95732a357

```
