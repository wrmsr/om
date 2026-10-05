case "$(dpkg --print-architecture)" in \
    amd64) CUDA_REPO_ARCH=x86_64 ;; \
    arm64) CUDA_REPO_ARCH=sbsa ;; \
    *) echo "Unsupported CUDA architecture: $(dpkg --print-architecture)" >&2 ; exit 1 ;; \
esac ;

curl -fsSLo /tmp/cuda-keyring.deb \
    "https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/${CUDA_REPO_ARCH}/cuda-keyring_1.1-1_all.deb" ;
sudo dpkg -i /tmp/cuda-keyring.deb ;
rm /tmp/cuda-keyring.deb ;

sudo apt-get update ;
sudo apt-get install -y --no-install-recommends \
    "cuda-toolkit-$(echo ${CUDA_VERSION} | tr . -)" \
;

echo '\n
export CUDA_HOME="/usr/local/cuda"\n
export PATH="$CUDA_HOME/bin:$PATH"\n
export LD_LIBRARY_PATH="/usr/local/nvidia/lib:/usr/local/nvidia/lib64:$CUDA_HOME/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"\n
export LIBRARY_PATH="$CUDA_HOME/lib64/stubs${LIBRARY_PATH:+:$LIBRARY_PATH}"\n
' >> ~/.bashrc ;
