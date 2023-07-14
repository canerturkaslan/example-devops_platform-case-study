# Stage 1: Build the application
FROM python:3.9-alpine AS builder

WORKDIR /app

COPY requirements.txt .

RUN apk add --no-cache gcc musl-dev && \
    pip install --no-cache-dir --user -r requirements.txt

COPY app.py .

# Stage 2: Create a lightweight image for the application
FROM python:3.9-alpine

WORKDIR /app

COPY --from=builder /root/.local /root/.local

COPY --from=builder /app .

ENV PATH=/root/.local/bin:$PATH

EXPOSE 5000

CMD ["python", "app.py"]

# In the first stage, the gcc and musl-dev packages are installed and the dependencies are installed under ~/.local with the --user flag. 
# In the second step, these dependencies are copied to /root/.local and added to the PATH environmental variable.
# It reduces the image size by using an Alpine-based multistage structure.