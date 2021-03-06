'''
We use this file to test the L_infty (L infinite) robustness 
Type 'python linf_attack.py {}.pt' ({} name of your model want to test) to run
This is based on https://adversarial-ml-tutorial.org
'''


import torch
import torch.nn as nn
import torch.optim as optim
from origin_train import data_process
import numpy as np
import argparse
from new_vgg_face import VGG_16
#from save_image import save_image 
#uncomment to show images  


def l_inf_pgd(model, X, y, epsilon=1, alpha=1, num_iter=20, randomize=False):
    """ Construct L_inf adversarial examples on the examples X """
    
    model.eval()
    mean = torch.Tensor(np.array([129.1863, 104.7624, 93.5940])).view(1, 3, 1, 1)
    de = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    mean = mean.to(de)
    if randomize:
        delta = torch.rand_like(X, requires_grad=True)
        delta.data = delta.data * 2 * epsilon - epsilon
        delta.data = (delta.data + X + mean).clamp(0,255)-(X+mean)
    else:
        delta = torch.zeros_like(X, requires_grad=True)
    for t in range(num_iter):
        loss = nn.CrossEntropyLoss()(model(X + delta ), y) #rgb to bgr 
        loss.backward()
        
        delta.data = (delta + alpha*delta.grad.detach().sign()).clamp(-epsilon,epsilon)
        delta.data = (delta.data +X + mean).clamp(0,255)-(X+mean)
        delta.grad.zero_()
    return delta.detach()




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='test')
    parser.add_argument("model", type=str, help="test_linf_robustness_of_model")
    args = parser.parse_args()
    
    eps     = [2   , 4   , 8  , 16 , 2   , 4   , 8  , 16 ] # eps is epsilon of the l infty bound 
    alpha   = [0.5 , 1   , 2  , 4  , 0.5 , 1   , 2  , 4  ] # alpha is learning rate 
    itera   = [7   , 7   , 7  , 7  , 20  , 20  , 20 , 20 ] # iterations to find optimal 
    restart = [1   , 1   , 1  , 1  , 1   , 1   , 1  , 1  ] # restart times, since we just do some standard check of our model, 
    #we do not use mutliple restarts, but you can change that if you want
    
    # change the hyperparmeters here if you want to test more 
    # delete some hyperparmeters could speed up 
    
    model = VGG_16() 
    model.load_state_dict(torch.load('../donemodel/'+args.model))
    
    print("test model is ", args.model)
    model.eval()
    batch_size = 32
    dataloaders,dataset_sizes =data_process(batch_size)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model.to(device)
    for i in range(len(eps)):
        correct = 0 
        total = 0 
        torch.manual_seed(12345)
        for data in dataloaders['test']:
            images, labels = data
            images = images[:,[2,1,0],:,:]
            images = images.to(device)
            labels = labels.to(device)
            total += labels.size(0)
            
            
            check_num = torch.zeros([1,labels.size(0)], dtype= torch.uint8,device=device)
            correct_num = torch.zeros([1,labels.size(0)], dtype= torch.uint8,device=device) + restart[i]
            for j in range(restart[i]):
                delta = l_inf_pgd(model, images, labels, eps[i], alpha[i] ,itera[i] ,True)
                with torch.no_grad():
                    model.eval()
                    outputs = model(images + delta)
                    # save_image("linf_attack",images+delta)
                    # uncomment to see images 
                    
                    _, predicted = torch.max(outputs.data, 1)

                    check_num += (predicted == labels)
            correct += (correct_num == check_num).sum().item()

        print("eps is ",eps[i],", alpha is ",alpha[i],", iteration is ",itera[i]," restart is ", restart[i])
        print('Accuracy of the network on the %s test images: %10.5f %%' % (total,100 * correct / total))










