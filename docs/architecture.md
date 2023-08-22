# Architecture
Skyplane performs high-performance, cost-efficient, bulk data transfers by parallelizing transfers, provisioning resources for transfers, and identifying optimal transfer paths. Skyplane profiles cloud network cost and throughput across regions, and borrows ideas from [RON](http://nms.csail.mit.edu/ron/) to identify optimal transfer paths across regions and cloud providers.

To learn about how Skyplane works, please see our talk here:
<iframe width="560" height="315" src="https://www.youtube-nocookie.com/embed/hOCrpcIBkAU" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

## On prem support
Skyplane now supports local to cloud object store transfers. For this, Skyplane defaults to awscli (for AWS), and gsutil (for GCP). [Let us know](https://github.com/skyplane-project/skyplane/issues/545) if you would like to see on-prem support for Azure.

## Transfer Integrity and Checksumming
Skyplane implements multiple measures to ensure the correctness of transfers. To prevent data corruption, such as bit flips or missing byte ranges, the platform calculates checksums for the source-region data and verifies these checksums before committing the data to the destination region. To eliminate the risk of dropped files during transfers, Skyplane queries the destination object store post-transfer, meticulously confirming that all files have been duplicated with precise file sizes intact. For comprehensive validation of checksums in whole-file transfers, Skyplane employs MD5 hashes at the source region. Once the data reaches the destination, these hashes are cross-verified directly within the destination object store. In cases involving multipart transfers, validation of hashes takes place within the destination virtual machine, a crucial step before any data is written to the object store.

## Security
Data transfers facilitated by Skyplane adhere to a stringent end-to-end encryption protocol. This entails encrypting all data chunks within the source region prior to transfer. These encrypted chunks maintain their secured state throughout their journey over the network, even when traversing relay regions, and they are only decrypted upon reaching the destination region.
It's important to note that within both the source and destination regions, data might be processed in plaintext. A clear example of this is the decryption of chunks at the destination gateways, followed by their insertion into the destination object store. For heightened security, the option exists for the utilizing application to opt for encrypted storage of data within the source object store. This decision ensures data remains encrypted even while situated in the source and destination regions.
To optimize efficiency for such scenarios, Skyplane offers the capability to disable its native encryption. This approach prevents unnecessary double encryption. The cryptographic keys integral to Skyplane's end-to-end encryption are generated at the client's end and subsequently transmitted to the gateways through a secure SSH connection.

HTTP/REST calls exchanged between gateways are independently encrypted using TLS.

Thanks to the encryption methods mentioned earlier, Skyplane provides a robust assurance of confidentiality against passive adversaries who might intercept data during transmission across the wide-area network and relay regions. While these adversaries are unable to access the actual content of the data, they could potentially gather the following information:

* The total volume of transferred data.
* The route taken by each chunk across the network and overlay path during the transfer.
* The dimensions of individual chunks (potentially linked to the size of the files or objects being moved).
* The timing of each chunk's journey between gateways and over the network.


## Firewalls

Skyplane adopts best practices to ensure data and gateway nodes are secure during transfers. In this section, we describe the design in-brief. Firewalls are enabled by default, and we advise you not to turn them off. This ensures not only is the data secure in flight, but also prevents gateways from being compromised.  Our approach of having unique `skyplane` VPC and firewalls  guarantees that your default networks remain untouched, and we have also architected it to allow for multiple simultaneous transfers! If you have any questions regarding the design and/or implementation we encourage you to open an issue with `[Firewall]` in the title.

### GCP
Skyplane creates a global VPC called [`skyplane`](https://github.com/skyplane-project/skyplane/blob/e5c97e007b69673558ade0396df490a98227dcc0/skyplane/compute/gcp/gcp_cloud_provider.py#L154) when it is invoked for the first time with a new subscription-id. Instances and firewall rules are applied on this VPC and do NOT interfere with the `default` GCP VPC. This ensures all the changes that Skyplane introduces are localized within the skyplane VPC - all instances and our firewalls rules only apply within the `skyplane` VPC. The `skyplane` global VPC consists of `skyplane` sub-nets for each region.

During every `skyplane` transfer, a new set of firewalls are [created](https://github.com/skyplane-project/skyplane/blob/e5c97e007b69673558ade0396df490a98227dcc0/skyplane/compute/gcp/gcp_cloud_provider.py#L218) that allow IPs of all instances that are involved in the transfer to exchange data with each other. These firewalls are set with priority 1000, and are revoked after the transfer completes. All instances can be accessed via `ssh` on port 22, and respond to `ICMP` packets to aid debugging.

### AWS

While GCP VPCs are Global, in AWS for every region that is involved in a transfer, Skyplane creates a `skyplane` [VPC](https://github.com/skyplane-project/skyplane/blob/e5c97e007b69673558ade0396df490a98227dcc0/skyplane/compute/aws/aws_cloud_provider.py#L93), and a [security group](https://github.com/skyplane-project/skyplane/blob/e5c97e007b69673558ade0396df490a98227dcc0/skyplane/compute/aws/aws_cloud_provider.py#L153) (SG). During transfers, firewall rules are [instantiated](https://github.com/skyplane-project/skyplane/blob/e5c97e007b69673558ade0396df490a98227dcc0/skyplane/compute/aws/aws_cloud_provider.py#L267) that allow all IPs of gateway instances involved in the transfer to relay data with each other. Post the transfer, the firewalls are [deleted](https://github.com/skyplane-project/skyplane/blob/e5c97e007b69673558ade0396df490a98227dcc0/skyplane/compute/aws/aws_cloud_provider.py#L283).

### Azure

Firewall support for Azure is in the roadmap.

## Large Objects
Skyplane breaks large objects into smaller sub-parts (currently AWS and GCP only) to improve transfer parallelism (also known as [striping](https://ieeexplore.ieee.org/document/1560006)).
