# Live dashboard for Covid-19 around the world

Source of data [here](https://github.com/CSSEGISandData/COVID-19).

# Run instruction
```bash
# build
docker build -t covid19-livedash

# run
docker run -p 8050:8050/tcp covid19-livedash
```