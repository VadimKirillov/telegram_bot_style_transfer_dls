from PIL import Image
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import torchvision.transforms as transforms
import torchvision.models as models
from torchvision.utils import save_image
import gc
import os
import logging

logging.basicConfig(level=logging.INFO)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
imsize = 512 if torch.cuda.is_available() else 200


def image_loader(image_name):
    transformation = transforms.Compose([
            transforms.Resize(imsize),
            transforms.CenterCrop(imsize),
            transforms.ToTensor()])
    image = Image.open(image_name)
    image = transformation(image).unsqueeze(0)
    return image.to(device, torch.float)


def gram_matrix(x):
    _, f_maps, h, w,  = x.size()
    x = x.view(f_maps, h * w)
    gram = torch.mm(x, x.t())
    return gram / (f_maps * h * w)


class ContentLoss(nn.Module):
    def __init__(self, target):
        super().__init__()
        self.target = target.detach()
        self.loss = F.mse_loss(self.target, self.target)

    def forward(self, inp):
        self.loss = F.mse_loss(inp, self.target)
        return inp


class StyleLoss(nn.Module):
    def __init__(self, target_feature):
        super().__init__()
        self.target = gram_matrix(target_feature).detach()
        self.loss = F.mse_loss(self.target, self.target)

    def forward(self, inp):
        gram = gram_matrix(inp)
        self.loss = F.mse_loss(gram, self.target)
        return inp


class NormalizationLayer(nn.Module):
    def __init__(self, mean, std):
        super().__init__()
        self.mean = mean.clone().detach().view(-1, 1, 1)
        self.std = std.clone().detach().view(-1, 1, 1)

    def forward(self, img):
        return (img - self.mean) / self.std


class NSTModel:
    def __init__(self, style_image, content_image):
        self.style = style_image
        self.content = content_image
        self.style_losses = []
        self.content_losses = []

        logging.warning("Creating VGG19 model...")
        feature_extractor = models.vgg19().features.to(device)
        logging.warning("Loading VGG19 weights...")
        feature_extractor.load_state_dict(torch.load("vgg19weights"))
        feature_extractor.eval()

        normalization_mean = torch.tensor([0.485, 0.456, 0.406]).to(device)
        normalization_std = torch.tensor([0.229, 0.224, 0.225]).to(device)

        normalization = NormalizationLayer(normalization_mean, normalization_std).to(device)

        self.model = nn.Sequential(normalization)

        content_layers = ["conv_4"]
        style_layers = ["conv_1", "conv_2", "conv_3", "conv_4", "conv_5"]

        logging.warning("Rearranging VGG19 model...")
        i = 0
        for layer in feature_extractor.children():
            if isinstance(layer, nn.Conv2d):
                i += 1
                name = "conv_{}".format(i)
            elif isinstance(layer, nn.ReLU):
                name = "relu_{}".format(i)
                layer = nn.ReLU(inplace=False)
            elif isinstance(layer, nn.MaxPool2d):
                name = "pool_{}".format(i)
                layer = torch.nn.AvgPool2d(kernel_size=2, stride=2, padding=0)
            self.model.add_module(name, layer)

            if name in content_layers:
                target = self.model(self.content).detach()
                content_loss = ContentLoss(target)
                self.model.add_module("content_loss_{}".format(i), content_loss)
                self.content_losses.append(content_loss)
            if name in style_layers:
                target_feature = self.model(self.style).detach()
                style_loss = StyleLoss(target_feature)
                self.model.add_module("style_loss_{}".format(i), style_loss)
                self.style_losses.append(style_loss)

        for i in range(len(self.model) - 1, -1, -1):
            if isinstance(self.model[i], ContentLoss) or isinstance(self.model[i], StyleLoss):
                break

        self.model = self.model[:(i + 1)].requires_grad_(False)
        logging.warning("Model is ready!")

    def fit(self, num_epochs=500, content_weight=1, style_weight=1000000):
        target = self.content.clone().requires_grad_(True).to(device)
        optimizer = optim.LBFGS([target])

        epoch = [0]
        logging.warning("Starting style transfer process...")
        while epoch[0] <= num_epochs:
            def get_loss():
                with torch.no_grad():
                    target.clamp_(0, 1)

                optimizer.zero_grad()
                self.model(target)
                style_score = 0
                content_score = 0

                for sl in self.style_losses:
                    style_score += sl.loss
                for cl in self.content_losses:
                    content_score += cl.loss

                style_score *= style_weight
                content_score *= content_weight

                loss = style_score + content_score
                loss.backward()

                epoch[0] += 1
                if epoch[0] % 50 == 0:
                    logging.warning(f"epoch {epoch}:")
                    logging.warning(f"Style Loss : {style_score.item():4f} Content Loss: {content_score.item():4f}")
                gc.collect()
                return style_score + content_score

            optimizer.step(get_loss)

        with torch.no_grad():
            target.clamp_(0, 1)

        return target


def run(style_image_path, content_image_path):
    style_img = image_loader(style_image_path)
    content_img = image_loader(content_image_path)

    nst_model = NSTModel(style_image=style_img, content_image=content_img)
    output = nst_model.fit()
    logging.warning("Image ready, saving...")
    save_image(output, "images/target/res.jpg")
    logging.warning("Image saved!")

    gc.collect()
    del nst_model
    os.remove(style_image_path)
    os.remove(content_image_path)
