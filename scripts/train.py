import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

from model.transformer import init_transformer
from utils.masks import create_mask
from utils.config import Config
from data.dataset import CopyDataset

import json

def train(model):
    model.to(Config.DEVICE)
    loss_fn = nn.CrossEntropyLoss(ignore_index=0)
    optimizer = optim.Adam(model.parameters(), lr=Config.LR)
    dataloader = DataLoader(CopyDataset(Config.VOCAB_SIZE, Config.len_of_sequence), batch_size=Config.BATCH_SIZE, shuffle=True)

    epoch_losses = []
    epoch_accuracies = []

    for epoch in range(Config.EPOCHS):
        model.train()
        total_loss = 0
        correct_tokens = 0
        total_tokens = 0

        for src, tgt in dataloader:
            src, tgt = src.to(Config.DEVICE), tgt.to(Config.DEVICE)
            tgt_input = tgt[:, :-1]
            tgt_output = tgt[:, 1:]

            src_mask, tgt_mask = create_mask(src, tgt_input)
            output = model(src, tgt_input, src_mask, tgt_mask)
            loss = loss_fn(output.view(-1, Config.VOCAB_SIZE), tgt_output.reshape(-1))

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

            # Accuracy: Compare predicted vs actual
            preds = output.argmax(dim=-1)
            correct_tokens += (preds == tgt_output).sum().item()
            total_tokens += tgt_output.numel()

        avg_loss = total_loss
        accuracy = correct_tokens / total_tokens
        epoch_losses.append(avg_loss)
        epoch_accuracies.append(accuracy)

        print(f"Epoch {epoch+1}: Loss = {avg_loss:.4f}, Accuracy = {accuracy:.4f}")

    # Save metrics and model
    metrics = {
        "losses": epoch_losses,
        "accuracies": epoch_accuracies
    }
    os.makedirs("assets", exist_ok=True)
    os.makedirs("checkpoints", exist_ok=True)
    with open("assets/metrics.json", "w") as f:
        json.dump(metrics, f)
    torch.save(model.state_dict(), "checkpoints/transformer.pt")
    print("✅ Model and metrics saved.")


if __name__ == "__main__":
    model = init_transformer(
        src_vocab_size=Config.VOCAB_SIZE,
        tgt_vocab_size=Config.VOCAB_SIZE,
        src_len_of_sequence=Config.len_of_sequence,
        tgt_len_of_sequence=Config.len_of_sequence
    )
    train(model)
