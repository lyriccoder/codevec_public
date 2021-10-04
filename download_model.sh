DICTIONARIES=models/java14m_trainable/dictionaries.bin
DATA=models/java14m_trainable/saved_model_iter3.release.data-00000-of-00001
INDEX=models/java14m_trainable/saved_model_iter3.release.index
META=models/java14m_trainable/saved_model_iter3.release.meta

if [ -f $DICTIONARIES && -f DATA && -f INDEX && -f META  ]; then
    echo "Model already downloaded"
else
    wget -nc https://s3.amazonaws.com/code2vec/model/java14m_model_trainable.tar.gz && tar -xvzf java14m_model_trainable.tar
fi
