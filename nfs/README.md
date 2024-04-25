# NFS

- references: 
    https://computingforgeeks.com/configure-nfs-as-kubernetes-persistent-volume-storage/#:~:text=Configure%20NFS%20as%20Kubernetes%20Persistent%20Volume%20Storage%201,Provisioner%20...%204%204.%20Test%20the%20setup%20
```
# in oneke, resize the existing disk to longhorn

on nfs-server:
-----------

$ apt update && install nfs-kernel-server -y

$ cat /etc/idmapd.conf
[General]

Verbosity = 0
# set your own domain here, if it differs from FQDN minus hostname
# Domain = localdomain

[Mapping]

Nobody-User = nobody
Nobody-Group = nogroup

$ cat /etc/exports


# /etc/exports: the access control list for filesystems which may be exported
#               to NFS clients.  See exports(5).
#
# Example for NFSv2 and NFSv3:
# /srv/homes       hostname1(rw,sync,no_subtree_check) hostname2(ro,sync,no_subtree_check)
#
# Example for NFSv4:
# /srv/nfs4        gss/krb5i(rw,sync,fsid=0,crossmnt,no_subtree_check)
# /srv/nfs4/homes  gss/krb5i(rw,sync,no_subtree_check)
#
/var/lib/longhorn  10.0.1.5/24(rw,sync,no_subtree_check)

$ chown -R nobody:nogroup /var/lib/longhorn

$ systemctl restart nfs-server
$ systemctl enable --now rpcbind nfs-server

on wokers (0-x):
----------
$ apt update && sudo apt install nfs-common -y
$ mkdir -p /mnt/nfs_longhorn
$ mount 10.0.1.5:/var/lib/longhorn /mnt/nfs_longhorn/

# add in /etc/fstab
10.0.1.5:/var/lib/longhorn /mnt/nfs_longhorn nfs defaults 0 0

on local:
----------
$ NFS_SERVER=10.0.1.5
$ NFS_EXPORT_PATH=/var/lib/longhorn

$ helm repo add nfs-subdir-external-provisioner https://kubernetes-sigs.github.io/nfs-subdir-external-provisioner/

$ helm -n  nfs-provisioner install nfs-provisioner-01 nfs-subdir-external-provisioner/nfs-subdir-external-provisioner \
    --set nfs.server=$NFS_SERVER \
    --set nfs.path=$NFS_EXPORT_PATH \
    --set storageClass.defaultClass=true \
    --set replicaCount=1 \
    --set storageClass.name=nfs-01 \
    --set storageClass.provisionerName=nfs-provisioner-01 \
    --kubeconfig KUBECONFIG_PATH \
    --create-namespace 
   
```
